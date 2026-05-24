import win32gui
import win32con
import win32api
import win32process
import mss
import numpy as np
import cv2
import time
import pydirectinput

# Fail-safe settings for pydirectinput
pydirectinput.FAILSAFE = False

def list_windows():
    """Returns a list of tuples (hwnd, title) of all visible, titled windows."""
    windows = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
        return True
    win32gui.EnumWindows(callback, None)
    # Sort by title alphabetically
    windows.sort(key=lambda w: w[1].lower())
    return windows

def get_window_rect(hwnd):
    """Returns (left, top, width, height) of the given window handle."""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bottom - top
        return left, top, w, h
    except Exception:
        return 0, 0, 0, 0

def focus_window(hwnd):
    """Brings the given window handle to the foreground and restores it if minimized."""
    try:
        # Check if minimized
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        # Bring to front
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.15) # Small delay to let the OS focus
        return True
    except Exception as e:
        print(f"Failed to focus window: {e}")
        return False

def capture_window(hwnd):
    """
    Captures the window using mss.
    Returns the BGR image or None if failed.
    """
    left, top, w, h = get_window_rect(hwnd)
    if w <= 0 or h <= 0:
        return None

    try:
        with mss.mss() as sct:
            monitor = {"top": top, "left": left, "width": w, "height": h}
            img = np.array(sct.grab(monitor))
            # mss returns BGRA, convert to BGR
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None

def click_foreground(hwnd, rel_x, rel_y, click_duration=0.05):
    """
    Simulates a hardware-level click on the foreground window using pydirectinput.
    Focuses the window first, moves mouse, clicks, and returns the cursor.
    """
    left, top, w, h = get_window_rect(hwnd)
    if w <= 0 or h <= 0:
        return False

    # Store original mouse position to restore it later
    try:
        orig_x, orig_y = win32api.GetCursorPos()
    except Exception:
        orig_x, orig_y = None, None

    # Focus the window
    focus_window(hwnd)

    # Calculate absolute screen coordinates
    abs_x = left + rel_x
    abs_y = top + rel_y

    try:
        # Move cursor using hardware DirectInput simulation
        pydirectinput.moveTo(int(abs_x), int(abs_y))
        time.sleep(0.05) # Crucial sleep for games to register the position first!
        pydirectinput.mouseDown()
        time.sleep(click_duration)
        pydirectinput.mouseUp()
        
        # Restore mouse position
        if orig_x is not None and orig_y is not None:
            time.sleep(0.05)
            pydirectinput.moveTo(int(orig_x), int(orig_y))
        return True
        
    except Exception as e:
        print(f"DirectInput click failed, falling back to mouse_event: {e}")
        try:
            # Fallback to standard mouse_event
            win32api.SetCursorPos((int(abs_x), int(abs_y)))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(click_duration)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            # Restore mouse position
            if orig_x is not None and orig_y is not None:
                time.sleep(0.05)
                win32api.SetCursorPos((orig_x, orig_y))
            return True
        except Exception as e2:
            print(f"Fallback click failed: {e2}")
            return False

def click_background(hwnd, rel_x, rel_y, click_duration=0.05):
    """
    Simulates a background click using SendMessage/PostMessage.
    Iterates recursively through child rendering windows to ensure emulator compatibility.
    """
    try:
        # Enumerate child windows (for emulator rendering canvases)
        children = []
        def callback(h, extra):
            children.append(h)
            return True
        try:
            win32gui.EnumChildWindows(hwnd, callback, None)
        except Exception:
            pass
        
        # Pack coordinates
        lparam = win32api.MAKELONG(int(rel_x), int(rel_y))
        
        # Send clicks to the main parent and all child handles (e.g. BlueStacks RenderWindow)
        targets = [hwnd] + children
        
        # Send WM_LBUTTONDOWN to all potential handles
        for target in targets:
            try:
                win32gui.PostMessage(target, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            except Exception:
                pass
                
        # Click press hold duration
        time.sleep(click_duration)
        
        # Send WM_LBUTTONUP to all potential handles
        for target in targets:
            try:
                win32gui.PostMessage(target, win32con.WM_LBUTTONUP, 0, lparam)
            except Exception:
                pass
                
        return True
    except Exception as e:
        print(f"Error performing background click: {e}")
        return False
