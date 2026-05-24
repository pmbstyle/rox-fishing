import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import sys
import time
import threading
import keyboard

# Import our custom modules
import win_utils
from fishing_bot import FishingBot

# Set up CustomTkinter appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")  # Modern blue theme by default

class RoxFishApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure Main Window
        self.title("ROX AUTOFISH PRO v1.0 - Ragnarok X: New Generation")
        self.geometry("1150x750")
        self.resizable(False, False)
        
        # Initialize Bot Core
        self.bot = FishingBot(
            log_callback=self.on_bot_log,
            preview_callback=self.on_bot_preview
        )
        
        # State variables
        self.window_list = []
        self.selected_hwnd = None
        self.calibration_image = None
        
        # Setup UI layout
        self.create_layout()
        
        # Refresh windows dropdown initial
        self.refresh_windows()
        
        # Bind global hotkeys (F5 for Start, F6 for Stop) in a separate thread
        self.setup_hotkeys()
        
        # Welcome message
        self.log_to_console("Welcome to ROX AUTOFISH PRO v1.0!")
        self.log_to_console("Step 1: Select your game window (or enable Simulation Mode to test).")
        self.log_to_console("Step 2: Click 'Calibrate' to locate the fishing button.")
        self.log_to_console("Step 3: Press F5 (Start) or F6 (Stop) to control the bot.")
        self.log_to_console("TIP: If hotkeys or clicks don't work, run this program as Administrator!")
        
    def create_layout(self):
        # Configure grid structure (1 row, 2 main columns: left options, right outputs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=4, minsize=450) # Left Controls
        self.grid_columnconfigure(1, weight=6, minsize=700) # Right Preview & Logs
        
        # --- LEFT PANEL (CONTROLS & SETTINGS) ---
        self.left_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#181920")
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        # Title Header Card
        self.title_card = ctk.CTkFrame(self.left_frame, corner_radius=10, fg_color="#212431", height=80)
        self.title_card.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.title_card.grid_propagate(False)
        self.title_card.grid_columnconfigure(0, weight=1)
        self.title_card.grid_rowconfigure(0, weight=1)
        
        # Title and Glow Light Container
        self.title_container = ctk.CTkFrame(self.title_card, fg_color="transparent")
        self.title_container.grid(row=0, column=0, padx=15, sticky="ew")
        
        self.app_title = ctk.CTkLabel(
            self.title_container, 
            text="ROX AUTOFISH PRO", 
            font=ctk.CTkFont(family="Outfit", size=22, weight="bold"),
            text_color="#ffffff"
        )
        self.app_title.pack(side="left", padx=5)
        
        # Glow Indicator Lamp
        self.status_lamp = ctk.CTkLabel(
            self.title_container,
            text="● STOPPED",
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            text_color="#7f8c8d"  # Gray initial
        )
        self.status_lamp.pack(side="right", padx=10)
        
        # Card 1: Target Window Selection
        self.window_card = ctk.CTkFrame(self.left_frame, corner_radius=10, fg_color="#212431")
        self.window_card.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.window_card.grid_columnconfigure(0, weight=1)
        
        self.win_card_title = ctk.CTkLabel(
            self.window_card, 
            text="TARGET WINDOW SELECTION", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3498db"
        )
        self.win_card_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
        
        # Window selector dropdown & refresh btn
        self.win_select_frame = ctk.CTkFrame(self.window_card, fg_color="transparent")
        self.win_select_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="ew")
        self.win_select_frame.grid_columnconfigure(0, weight=1)
        
        self.window_dropdown = ctk.CTkComboBox(
            self.win_select_frame, 
            values=[], 
            command=self.on_window_selected,
            height=35
        )
        self.window_dropdown.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.refresh_btn = ctk.CTkButton(
            self.win_select_frame, 
            text="Refresh ⟳", 
            width=80, 
            height=35,
            command=self.refresh_windows,
            fg_color="#34495e",
            hover_color="#2c3e50"
        )
        self.refresh_btn.grid(row=0, column=1, sticky="e")
        
        # Selected window label info
        self.window_info_label = ctk.CTkLabel(
            self.window_card,
            text="No active window selected.",
            font=ctk.CTkFont(size=11),
            text_color="#95a5a6",
            justify="left"
        )
        self.window_info_label.grid(row=2, column=0, columnspan=2, padx=15, pady=(2, 8), sticky="w")
        
        # Simulation Mode switch inside window card
        self.sim_switch = ctk.CTkSwitch(
            self.window_card, 
            text="Enable Test / Simulation Mode", 
            command=self.toggle_simulation,
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color="#e67e22"
        )
        self.sim_switch.grid(row=3, column=0, columnspan=2, padx=15, pady=(5, 12), sticky="w")
        
        # Card 2: Configuration settings sliders
        self.config_card = ctk.CTkFrame(self.left_frame, corner_radius=10, fg_color="#212431")
        self.config_card.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        self.config_card.grid_columnconfigure(0, weight=1)
        
        self.config_card_title = ctk.CTkLabel(
            self.config_card, 
            text="FISHING PARAMETERS CONFIGURATION", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1abc9c"
        )
        self.config_card_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Custom parameters setup
        # Parameter: Click Offset
        self.offset_label = ctk.CTkLabel(self.config_card, text="Click Random Offset: ±8 px", font=ctk.CTkFont(size=11))
        self.offset_label.grid(row=1, column=0, padx=15, pady=(5, 0), sticky="w")
        self.offset_slider = ctk.CTkSlider(self.config_card, from_=1, to=20, command=self.update_offset)
        self.offset_slider.set(8)
        self.offset_slider.grid(row=2, column=0, padx=15, pady=(0, 8), sticky="ew")
        
        # Parameter: Human Delay Range
        self.delay_label = ctk.CTkLabel(self.config_card, text="Cast Click Delay: 100ms - 300ms", font=ctk.CTkFont(size=11))
        self.delay_label.grid(row=3, column=0, padx=15, pady=(5, 0), sticky="w")
        self.delay_slider = ctk.CTkSlider(self.config_card, from_=50, to=1000, command=self.update_delay)
        self.delay_slider.set(300) # set max boundary
        self.delay_slider.grid(row=4, column=0, padx=15, pady=(0, 8), sticky="ew")
        
        # Parameter: Green Detection Threshold
        self.green_label = ctk.CTkLabel(self.config_card, text="Green Pixel Sensitivity: 1500px", font=ctk.CTkFont(size=11))
        self.green_label.grid(row=5, column=0, padx=15, pady=(5, 0), sticky="w")
        self.green_slider = ctk.CTkSlider(self.config_card, from_=500, to=15000, command=self.update_green)
        self.green_slider.set(1500)
        self.green_slider.grid(row=6, column=0, padx=15, pady=(0, 8), sticky="ew")
        
        # Parameter: Click Mode SegBtn
        self.click_mode_label = ctk.CTkLabel(self.config_card, text="Click Mechanism Mode:", font=ctk.CTkFont(size=11))
        self.click_mode_label.grid(row=7, column=0, padx=15, pady=(5, 0), sticky="w")
        self.click_mode_btn = ctk.CTkSegmentedButton(
            self.config_card, 
            values=["Foreground (100% Ok)", "Background (Beta)"],
            command=self.update_click_mode
        )
        self.click_mode_btn.set("Foreground (100% Ok)")
        self.click_mode_btn.grid(row=8, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        
        # --- RIGHT PANEL (LIVE PREVIEW & LOGS) ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#181920")
        self.right_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=4) # Preview Card
        self.right_frame.grid_rowconfigure(1, weight=6) # Log Card
        
        # Card 3: Calibration Preview Card
        self.preview_card = ctk.CTkFrame(self.right_frame, corner_radius=10, fg_color="#212431")
        self.preview_card.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        self.preview_card.grid_columnconfigure(0, weight=1) # preview details
        self.preview_card.grid_columnconfigure(1, weight=1) # controls
        
        # Column 0: Preview Box
        self.preview_box = ctk.CTkFrame(self.preview_card, corner_radius=8, fg_color="#12131a", width=220, height=220)
        self.preview_box.grid(row=0, column=0, padx=15, pady=15, sticky="n")
        self.preview_box.grid_propagate(False)
        
        # Preview Label (holds image)
        self.preview_label = ctk.CTkLabel(
            self.preview_box, 
            text="No Action Button\nPreview Available\n\n[Click Calibrate]",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Column 1: Calibration Controls
        self.cal_controls = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.cal_controls.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        self.preview_title = ctk.CTkLabel(
            self.cal_controls, 
            text="BUTTON CALIBRATION", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#9b59b6",
            anchor="w"
        )
        self.preview_title.pack(fill="x", pady=(0, 10))
        
        self.preview_desc = ctk.CTkLabel(
            self.cal_controls,
            text="Calculates coordinates of your game's action button using intelligent templates. Calibration is highly recommended before starting.",
            font=ctk.CTkFont(size=11),
            text_color="#95a5a6",
            justify="left",
            wraplength=280
        )
        self.preview_desc.pack(fill="x", pady=(0, 15))
        
        self.cal_btns_frame = ctk.CTkFrame(self.cal_controls, fg_color="transparent")
        self.cal_btns_frame.pack(fill="x", pady=5)
        
        self.calibrate_btn = ctk.CTkButton(
            self.cal_btns_frame, 
            text="CALIBRATE BUTTON", 
            fg_color="#9b59b6", 
            hover_color="#8e44ad",
            font=ctk.CTkFont(weight="bold"),
            height=38,
            command=self.run_calibration
        )
        self.calibrate_btn.pack(fill="x", pady=5)
        
        # Card 4: Console Log Card
        self.log_card = ctk.CTkFrame(self.right_frame, corner_radius=10, fg_color="#212431")
        self.log_card.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.log_card.grid_columnconfigure(0, weight=1)
        self.log_card.grid_rowconfigure(1, weight=1)
        
        # Console Header
        self.console_header_frame = ctk.CTkFrame(self.log_card, fg_color="transparent")
        self.console_header_frame.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        self.console_title = ctk.CTkLabel(
            self.console_header_frame, 
            text="LIVE LOG TERMINAL CONSOLE", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e67e22"
        )
        self.console_title.pack(side="left")
        
        self.clear_btn = ctk.CTkButton(
            self.console_header_frame,
            text="Clear",
            width=50,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.clear_console
        )
        self.clear_btn.pack(side="right")
        
        # Scrollable console box
        self.console_box = ctk.CTkTextbox(
            self.log_card, 
            fg_color="#12131a", 
            text_color="#2ecc71", # Hacker Green logs
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8
        )
        self.console_box.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        self.console_box.configure(state="disabled") # Read only initially
        
        # Large Start / Stop Button panel at the bottom of the log card
        self.control_buttons_frame = ctk.CTkFrame(self.log_card, fg_color="transparent")
        self.control_buttons_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.control_buttons_frame.grid_columnconfigure(0, weight=1)
        self.control_buttons_frame.grid_columnconfigure(1, weight=1)
        
        self.start_btn = ctk.CTkButton(
            self.control_buttons_frame,
            text="START BOT (F5)",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            command=self.start_bot
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.stop_btn = ctk.CTkButton(
            self.control_buttons_frame,
            text="STOP BOT (F6)",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            command=self.stop_bot
        )
        self.stop_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
    # --- HELPER FUNCTIONS ---
    
    def log_to_console(self, text):
        """Append text to console safely in Tkinter text thread."""
        self.console_box.configure(state="normal")
        self.console_box.insert("end", text + "\n")
        self.console_box.see("end")
        self.console_box.configure(state="disabled")
        
    def clear_console(self):
        self.console_box.configure(state="normal")
        self.console_box.delete("1.0", "end")
        self.console_box.configure(state="disabled")
        
    def on_bot_log(self, text):
        """Callback from bot thread, ensures safe UI update."""
        self.after(0, lambda: self.log_to_console(text))
        
        # Automatically update status indicator lamp based on state changes in log text
        if "[Casting]" in text or "CATCHING FISH!" in text:
            self.after(0, lambda: self.update_status_lamp("RUNNING", "#2ecc71"))
        elif "WAITING_FOR_BITE" in text or "waiting for fish to bite" in text:
            self.after(0, lambda: self.update_status_lamp("WAITING", "#3498db"))
        elif "entering cooldown" in text or "COOLDOWN" in text:
            self.after(0, lambda: self.update_status_lamp("COOLDOWN", "#f1c40f"))
            
    def on_bot_preview(self, cropped_bgr):
        """Callback from bot thread with the cropped button image."""
        self.after(0, lambda: self.update_preview_image(cropped_bgr))
        
    def update_preview_image(self, cropped_bgr):
        """Converts opencv BGR crop to CTkImage and renders it."""
        try:
            # Convert BGR to RGB
            rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = pil_img.resize((180, 180), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(180, 180))
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img
        except Exception as e:
            print(f"Error updating preview: {e}")
            
    def update_status_lamp(self, text, color):
        """Updates top status label (neon glow)."""
        self.status_lamp.configure(text=f"● {text}", text_color=color)

    # --- ACTION HANDLERS ---
    
    def refresh_windows(self):
        """Refreshes the window list in the dropdown."""
        self.window_list = win_utils.list_windows()
        
        # Build dropdown options
        options = []
        default_index = -1
        
        for idx, (hwnd, title) in enumerate(self.window_list):
            options.append(f"{title} (HWND: {hwnd})")
            # Auto-detect Ragnarok X
            if "ragnarok x" in title.lower():
                default_index = idx
                
        self.window_dropdown.configure(values=options)
        
        if options:
            if default_index != -1:
                self.window_dropdown.set(options[default_index])
                self.on_window_selected(options[default_index])
            else:
                self.window_dropdown.set(options[0])
                self.on_window_selected(options[0])
        else:
            self.window_dropdown.configure(values=["No windows found"])
            self.window_dropdown.set("No windows found")
            self.selected_hwnd = None
            self.window_info_label.configure(text="No active window selected.", text_color="#95a5a6")
            
        self.log_to_console("Window list refreshed.")
        
    def on_window_selected(self, value):
        """Fires when user selects a window from the list."""
        if not self.window_list or value == "No windows found":
            self.selected_hwnd = None
            return
            
        try:
            # Extract HWND from string "Title (HWND: 12345)"
            hwnd_part = value.split("(HWND: ")[1].replace(")", "")
            hwnd = int(hwnd_part)
            
            # Find the match
            for h, title in self.window_list:
                if h == hwnd:
                    self.selected_hwnd = h
                    self.bot.hwnd = h
                    self.bot.window_title = title
                    
                    # Update label info
                    left, top, w, h_dim = win_utils.get_window_rect(h)
                    self.window_info_label.configure(
                        text=f"Target: {title}\nHWND: {h} | Pos: ({left}, {top}) | Size: {w}x{h_dim}",
                        text_color="#2ecc71"
                    )
                    self.log_to_console(f"Selected target window: '{title}' (HWND: {h})")
                    
                    # Clear button rect when window changes to force recalibration
                    self.bot.button_rect = None
                    break
        except Exception as e:
            self.log_to_console(f"Error parsing selected window: {e}")
            
    def toggle_simulation(self):
        """Toggles simulation test mode."""
        enabled = self.sim_switch.get() == 1
        self.bot.set_simulation_mode(enabled)
        
        if enabled:
            self.window_info_label.configure(
                text="TEST MODE ACTIVE\nUsing images/window.png as mock screen.",
                text_color="#e67e22"
            )
            # Reset button calibration for simulation
            self.bot.button_rect = None
        else:
            # Re-trigger selection of active window
            current_val = self.window_dropdown.get()
            self.on_window_selected(current_val)
            
    def run_calibration(self):
        """Triggers manual button calibration in a safe thread."""
        def cal_thread():
            if not self.bot.simulation_mode and not self.selected_hwnd:
                self.after(0, lambda: self.log_to_console("ERROR: Please select a valid game window before calibrating!"))
                return
                
            self.after(0, lambda: self.update_status_lamp("CALIBRATING", "#f39c12"))
            success = self.bot.calibrate()
            
            if success:
                self.after(0, lambda: self.update_status_lamp("CALIBRATED", "#9b59b6"))
            else:
                self.after(0, lambda: self.update_status_lamp("CAL. FAILED", "#e74c3c"))
                
        threading.Thread(target=cal_thread, daemon=True).start()
        
    def start_bot(self):
        """Starts the bot execution."""
        if self.bot.running:
            return
            
        if not self.bot.simulation_mode and not self.selected_hwnd:
            self.log_to_console("ERROR: Select a game window first.")
            return
            
        self.update_status_lamp("RUNNING", "#2ecc71")
        self.bot.start()
        
    def stop_bot(self):
        """Stops the bot execution."""
        if not self.bot.running:
            return
            
        self.bot.stop()
        self.update_status_lamp("STOPPED", "#7f8c8d")
        
    # --- CONFIGURATION HANDLERS ---
    
    def update_offset(self, value):
        offset = int(value)
        self.bot.click_offset = offset
        self.offset_label.configure(text=f"Click Random Offset: ±{offset} px")
        
    def update_delay(self, value):
        max_delay = int(value)
        # Scale min delay to be proportional (e.g. 1/3 of max delay)
        min_delay = max(50, int(max_delay / 3))
        self.bot.click_delay_min = min_delay
        self.bot.click_delay_max = max_delay
        self.delay_label.configure(text=f"Cast Click Delay: {min_delay}ms - {max_delay}ms")
        
    def update_green(self, value):
        green_threshold = int(value)
        self.bot.green_threshold = green_threshold
        self.green_label.configure(text=f"Green Pixel Sensitivity: {green_threshold}px")
        
    def update_click_mode(self, value):
        if "Foreground" in value:
            self.bot.click_mode = "foreground"
            self.log_to_console("Click mechanism updated to: Foreground (Window will be activated on clicks)")
        else:
            self.bot.click_mode = "background"
            self.log_to_console("Click mechanism updated to: Background (Experimental postMessage mode)")

    # --- GLOBAL HOTKEYS ---
    
    def setup_hotkeys(self):
        """Registers F5 and F6 keyboard hooks in a background daemon thread."""
        def hotkey_daemon():
            # global hooks using keyboard module
            keyboard.add_hotkey('f5', self.trigger_f5_start)
            keyboard.add_hotkey('f6', self.trigger_f6_stop)
            
            # Keep thread running
            keyboard.wait()
            
        t = threading.Thread(target=hotkey_daemon, daemon=True)
        t.start()
        
    def trigger_f5_start(self):
        # Must execute on main thread to avoid tk thread-safety bugs
        self.after(0, self.start_bot)
        
    def trigger_f6_stop(self):
        self.after(0, self.stop_bot)

if __name__ == "__main__":
    app = RoxFishApp()
    app.mainloop()
