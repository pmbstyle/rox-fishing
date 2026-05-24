import cv2
import numpy as np
import time
import os
import random
import threading
import win_utils

class FishingBot:
    def __init__(self, log_callback=None, preview_callback=None):
        self.log_callback = log_callback
        self.preview_callback = preview_callback
        
        # Load templates
        self.img_dir = r"c:\Code\tmp\rox-fishing\images"
        self.idle_path = os.path.join(self.img_dir, "idle.png")
        self.catch_path = os.path.join(self.img_dir, "catch.png")
        
        self.idle_img = cv2.imread(self.idle_path)
        self.catch_img = cv2.imread(self.catch_path)
        
        if self.idle_img is not None:
            self.idle_gray = cv2.cvtColor(self.idle_img, cv2.COLOR_BGR2GRAY)
        else:
            self.idle_gray = None
            self.log("ERROR: idle.png template not found!")
            
        if self.catch_img is not None:
            self.catch_gray = cv2.cvtColor(self.catch_img, cv2.COLOR_BGR2GRAY)
        else:
            self.catch_gray = None
            self.log("ERROR: catch.png template not found!")
            
        # Target Window
        self.hwnd = None
        self.window_title = ""
        
        # Settings
        self.click_offset = 8             # Max pixel offset for click (± pixels)
        self.click_delay_min = 100        # min delay before clicking in ms
        self.click_delay_max = 300        # max delay before clicking in ms
        self.confidence_threshold = 0.70  # Template matching confidence
        self.check_rate = 30.0            # Capture checks per second (Hz) - increased to 30 for fast reaction
        self.click_mode = "foreground"    # "foreground" or "background"
        self.green_threshold = 1500       # Number of green pixels to trigger catch (reduced for early bite detection)
        
        # Simulation Mode settings
        self.simulation_mode = False
        self.mock_image_path = os.path.join(self.img_dir, "window.png")
        self.mock_image = None
        
        # Bot State
        self.running = False
        self.state = "IDLE"  # IDLE, CALIBRATING, WAITING_FOR_BITE, COOLDOWN
        self.button_rect = None  # (x, y, w, h) relative to window
        
        # Thread control
        self.thread = None
        
    def log(self, message):
        """Helper to send logs to UI."""
        if self.log_callback:
            timestamp = time.strftime("%H:%M:%S")
            self.log_callback(f"[{timestamp}] {message}")
        else:
            print(message)
            
    def update_preview(self, cropped):
        """Helper to send crop preview to UI."""
        if self.preview_callback and cropped is not None:
            self.preview_callback(cropped)

    def set_simulation_mode(self, enabled):
        self.simulation_mode = enabled
        if enabled:
            self.log(f"Simulation Mode ENABLED. Using {os.path.basename(self.mock_image_path)}")
            self.mock_image = cv2.imread(self.mock_image_path)
            if self.mock_image is None:
                self.log("ERROR: Failed to load mock window image!")
        else:
            self.log("Simulation Mode DISABLED. Capturing live window.")
            self.mock_image = None

    def capture_frame(self):
        """Captures active game frame depending on mode (live vs simulation)."""
        if self.simulation_mode:
            if self.mock_image is not None:
                return self.mock_image.copy()
            else:
                return None
        else:
            if not self.hwnd:
                return None
            return win_utils.capture_window(self.hwnd)

    def calibrate(self):
        """
        Locates the action button in the window.
        Uses template matching with idle.png (and catch.png as fallback).
        """
        self.state = "CALIBRATING"
        self.log("Starting calibration...")
        
        frame = self.capture_frame()
        if frame is None:
            self.log("Calibration failed: Unable to capture game frame.")
            self.state = "IDLE"
            return False
            
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Try matching idle template
        if self.idle_gray is not None:
            res = cv2.matchTemplate(frame_gray, self.idle_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= self.confidence_threshold:
                h, w = self.idle_gray.shape
                self.button_rect = (max_loc[0], max_loc[1], w, h)
                self.log(f"Calibration successful! Found IDLE button at x={max_loc[0]}, y={max_loc[1]}, w={w}, h={h} (Confidence: {max_val:.2f})")
                self.state = "READY"
                # Send initial preview
                cropped = frame[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
                self.update_preview(cropped)
                return True
                
        # 2. Fallback to matching catch template (if rod is already cast)
        if self.catch_gray is not None:
            self.log("Idle button not found. Trying catch button fallback...")
            res = cv2.matchTemplate(frame_gray, self.catch_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= self.confidence_threshold:
                h, w = self.catch_gray.shape
                self.button_rect = (max_loc[0], max_loc[1], w, h)
                self.log(f"Calibration successful (Fallback)! Found CATCH button at x={max_loc[0]}, y={max_loc[1]}, w={w}, h={h} (Confidence: {max_val:.2f})")
                self.state = "READY"
                cropped = frame[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
                self.update_preview(cropped)
                return True
                
        self.log(f"Calibration failed: Action button not found (Max match confidence: {max_val:.2f}, Threshold: {self.confidence_threshold:.2f}). Please ensure game is visible.")
        self.state = "IDLE"
        return False

    def perform_click(self, instant=False):
        """Simulates a natural click with randomized offset and optional delay."""
        if not self.button_rect:
            return
            
        bx, by, bw, bh = self.button_rect
        
        # Calculate base center coordinates
        center_x = bx + bw / 2
        center_y = by + bh / 2
        
        # Add random human offset (slightly smaller for catches to keep accuracy)
        offset = self.click_offset if not instant else max(2, int(self.click_offset / 2))
        offset_x = random.randint(-offset, offset)
        offset_y = random.randint(-offset, offset)
        
        rel_click_x = center_x + offset_x
        rel_click_y = center_y + offset_y
        
        if not instant:
            # Randomize click delay before execution (only for casting to simulate human behavior)
            delay_ms = random.randint(self.click_delay_min, self.click_delay_max)
            time.sleep(delay_ms / 1000.0)
            self.log(f"Clicking action button at relative pos ({rel_click_x:.1f}, {rel_click_y:.1f}) [Delay: {delay_ms}ms, Offset: {offset_x, offset_y}px]")
        else:
            # Lightning-fast catch click with zero artificial delay
            self.log(f"⚡ INSTANT catch click triggered at relative pos ({rel_click_x:.1f}, {rel_click_y:.1f}) [Offset: {offset_x, offset_y}px]")
        
        if self.simulation_mode:
            self.log("[Simulation] Simulated click completed.")
            # In simulation, we fake the button change for demonstration
            return True
            
        if self.click_mode == "foreground":
            return win_utils.click_foreground(self.hwnd, rel_click_x, rel_click_y)
        else:
            return win_utils.click_background(self.hwnd, rel_click_x, rel_click_y)

    def detect_green_pixels(self, cropped_bgr):
        """Counts the green pixels inside the cropped button region."""
        hsv = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2HSV)
        
        # Green in HSV: Hue ~35-85, Saturation ~40-255, Value ~40-255
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_count = np.sum(mask > 0)
        return green_count, mask

    def start(self):
        """Starts the background bot thread."""
        if self.running:
            return
            
        if not self.simulation_mode and not self.hwnd:
            self.log("ERROR: No game window selected. Cannot start.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.thread.start()
        self.log("Bot process STARTED.")

    def stop(self):
        """Stops the bot thread."""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.state = "IDLE"
        self.log("Bot process STOPPED.")

    def _bot_loop(self):
        """Core background thread state machine."""
        consecutive_failures = 0
        
        while self.running:
            loop_start_time = time.time()
            
            # 1. Grab screen frame
            frame = self.capture_frame()
            if frame is None:
                consecutive_failures += 1
                if consecutive_failures % 10 == 0:
                    self.log(f"Warning: Failed to capture screen {consecutive_failures} times in a row.")
                time.sleep(0.5)
                continue
            consecutive_failures = 0
            
            # 2. Check calibration
            if not self.button_rect:
                self.log("Bot is active but not calibrated. Running calibration...")
                calibrated = self.calibrate()
                if not calibrated:
                    self.log("Calibration failed. Retrying in 3 seconds...")
                    time.sleep(3.0)
                    continue
                # Calibration succeeded, continue loop with calibrated rect
                continue
                
            # 3. Crop button area
            bx, by, bw, bh = self.button_rect
            # Safety bounds check
            frame_h, frame_w, _ = frame.shape
            if bx + bw > frame_w or by + bh > frame_h:
                self.log("Warning: Calibrated button is out of capture bounds! Window might have resized. Recalibrating...")
                self.button_rect = None
                continue
                
            cropped = frame[by:by+bh, bx:bx+bw]
            self.update_preview(cropped)
            
            # 4. Check Catch State (Is the fish biting?)
            # We look for green pixels in the cropped button area
            green_count, mask = self.detect_green_pixels(cropped)
            
            if green_count >= self.green_threshold:
                # FISH BITE! Catch it!
                self.state = "CATCHING"
                self.log(f"BITE DETECTED! Green pixels: {green_count} (threshold: {self.green_threshold}). CATCHING FISH!")
                
                # Perform Catch click!
                self.perform_click(instant=True)
                
                # Cooldown after catch to allow reel animation and prevent double clicks
                self.state = "COOLDOWN"
                cooldown_time = 3.5  # standard Ragnarok X catching animation
                self.log(f"Catch click complete. Entering cooldown for {cooldown_time}s...")
                
                # In simulation mode, we can simulate the mock image transitioning back to idle
                # to show a fully working cycle to the user!
                if self.simulation_mode:
                    # Let's show a simulated transition
                    time.sleep(cooldown_time)
                    self.log("[Simulation] Cooldown finished. Simulating idle button state.")
                else:
                    time.sleep(cooldown_time)
                
                self.state = "WAITING_FOR_BITE"
                self.log("Cooldown finished. Ready for next cycle.")
                continue
                
            # 5. Check if we need to Cast (Is the button in the idle state?)
            # To cast the rod, we check if the cropped button matches idle.png template
            cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            
            # We match the idle template inside the cropped button to see if it is idle
            # Note: since the crop is roughly the same size as the idle template, we check standard correlation
            if self.idle_gray is not None:
                # Ensure sizes are compatible
                cw_h, cw_w = cropped_gray.shape
                it_h, it_w = self.idle_gray.shape
                
                if cw_h >= it_h and cw_w >= it_w:
                    res = cv2.matchTemplate(cropped_gray, self.idle_gray, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(res)
                else:
                    max_val = 0.0
            else:
                max_val = 0.0
                
            if self.state == "READY" or self.state == "IDLE":
                # Bot just started or is ready. Check if it's currently idle and we can cast.
                if max_val >= self.confidence_threshold:
                    self.log(f"Action button matches IDLE state (Confidence: {max_val:.2f}). Casting fishing rod...")
                    self.state = "CASTING"
                    self.perform_click()
                    
                    # Casting animation delay
                    cast_delay = 2.0
                    self.log(f"Rod casted! Waiting {cast_delay}s for casting animation...")
                    time.sleep(cast_delay)
                    
                    self.state = "WAITING_FOR_BITE"
                    self.log("Now waiting for fish to bite (monitoring for green colors)...")
                    continue
                else:
                    # If not idle, maybe we are already in the water?
                    self.log("Rod appears to be already casted. Transitioning directly to waiting for bite...")
                    self.state = "WAITING_FOR_BITE"
                    continue
                    
            elif self.state == "WAITING_FOR_BITE":
                # While waiting, if the button becomes idle again (e.g. fish escaped or missed bite),
                # we should recast!
                if max_val >= 0.85: # High threshold for idle detection while fishing
                    self.log("Rod is not in water anymore (Idle button detected). Recasting...")
                    self.state = "CASTING"
                    self.perform_click()
                    time.sleep(2.0)
                    self.state = "WAITING_FOR_BITE"
                    continue
                    
            # 6. Throttle the loop according to target rate
            elapsed = time.time() - loop_start_time
            sleep_needed = (1.0 / self.check_rate) - elapsed
            if sleep_needed > 0:
                time.sleep(sleep_needed)
                
        self.state = "IDLE"
