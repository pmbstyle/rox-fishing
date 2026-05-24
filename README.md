# 🎣 ROX Autofish Pro

**ROX Autofish Pro** is a modern, high-speed, and reliable auto-fishing bot designed specifically for **Ragnarok X: New Generation**. It features a stunning Premium Dark GUI built with CustomTkinter, neon status indicators, a live visual calibration preview, and a real-time console terminal.

The bot is designed with ultra-low latency reaction and uses hardware-level input simulation (DirectInput scan codes) to bypass game click-blocking mechanisms.

---

## ✨ Features

*   **🖥️ CustomTkinter Premium GUI**: A beautiful, fluid dark theme featuring responsive sliders, segmented selectors, and clear visual organization.
*   **🎯 Intelligent Auto-Calibration (OpenCV Template Matching)**: The bot automatically detects the exact position of the fishing action button on your screen, regardless of resolution or window size. No manual coordinate input required!
*   **⚡ Ultra-Fast Reaction (HSV Bite Detection)**: Analyzes the cropped button region 30 times per second. The moment the green marker appears during a bite, the bot sends a click within milliseconds, guaranteeing a 100% catch rate.
*   **👤 Humanized Interactions**: Randomized delay before casting (ranging from 100ms to 1000ms) and random click coordinate offsets (±8 pixels) prevent bot detection.
*   **🎥 Real-Time Preview**: An interactive canvas displays the active button region in real-time, allowing you to visually monitor what the bot sees.
*   **⌨️ Global Hotkeys**: Start (`F5`) and stop (`F6`) hooks run in the background globally—even when the bot window is minimized or you are actively in-game.
*   **🧪 Test / Simulation Mode**: Allows you to safely test calibration and color detection algorithms on static screenshot files without running the actual game.
*   **⚙️ Click Mechanisms**:
    *   *Foreground Mode* (Recommended) — Focuses the game window and executes ultra-fast, hardware-level DirectInput clicks.
    *   *Background Mode* (Experimental) — Recursively resolves and sends mouse events directly to the emulator's child rendering canvas handles, allowing you to run the bot on the background while using your PC.

---

## 🛠️ Requirements & Installation

The application requires **Python 3.10+** installed on Windows.

1. Clone the repository:
   ```bash
   git clone https://github.com/pmbstyle/rox-fishing.git
   cd rox-fishing
   ```

2. Install all required dependencies:
   ```bash
   pip install customtkinter opencv-python pillow pywin32 mss pydirectinput keyboard
   ```

---

## 🚀 How to Use

> [!IMPORTANT]
> **Run as Administrator**:
> If your game client or emulator runs with Administrator privileges (highly common for anti-cheat and emulators), Windows will block any mouse events or hotkeys simulated by lower-privileged programs.
> 
> To bypass Windows UIPI protections, **you must open your terminal (PowerShell / Command Prompt) as Administrator** before running the bot!

1. Open PowerShell / Command Prompt as **Administrator**.
2. Run the application:
   ```bash
   python main.py
   ```
3. Select your game window (**Ragnarok X**) from the dropdown menu at the top.
4. Click **CALIBRATE BUTTON** to allow the bot to locate the action button.
5. Press **F5** (or click **START**) to begin auto-fishing.
6. Press **F6** (or click **STOP**) at any time to immediately halt the bot.

---

## ⚙️ Configuration Parameters

*   **Click Random Offset** — Radius in pixels for randomized click variance (prevents pixel-point pattern detection).
*   **Cast Click Delay** — Range of randomized delay before casting the fishing rod.
*   **Green Pixel Sensitivity** — Threshold for green pixel triggers (lower values trigger catch faster on early bite frames).
*   **Click Mechanism Mode**:
    *   *Foreground* — Standard DirectInput click. Brings the window to the front, clicks, and returns the cursor to its original position.
    *   *Background* — PostMessage click. Emulates clicks silently on the background without interrupting your mouse cursor.
