# 🌅 sunii

**sunii** is a lightweight Windows utility that automatically adjusts your screen brightness based on a customizable day/night schedule. With a clean, transparent UI and tray support, it runs quietly in the background — keeping your eyes (and workflow) happy.

---

##  Features

- Schedule night and day screen brightness separately
- Adjustable per-minute precision
- Auto-switch between light and dark UI themes
- Fully portable `.exe` version available
- Tray icon with left-click restore
- Settings are saved locally in a config file
- Zero telemetry, zero dependencies beyond Python packages

---

##  Usage

Once launched:

1. **Set your desired schedule**:
   - Choose when “night mode” starts (e.g., 8:00 PM).
   - Choose when “day mode” starts (e.g., 7:00 AM).
2. **Adjust screen brightness**:
   - Set separate brightness levels for day and night.
   - Sliders range from 0 to 100.
3. **Click “Save Settings”** to store your preferences.
4. **Click “Start sunii”** to activate the background scheduler.
5. Minimize the app — it will go to the system tray.

### Tray Behavior
-  **Left-click** the tray icon to restore the window.
-  **Right-click** for the “Restore” and “Exit” options.

Settings are saved locally in `sunii_config.ini`.

---

##  Getting Started

###  Requirements

- Python 3.9 or higher (Windows only)
- Windows 10/11 with WMI brightness control support

###  Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/yourusername/sunii.git
cd sunii
pip install -r requirements.txt
python sunii.py
```

---

##  Building a Portable Executable

To generate `sunii.exe`:

```bash
pyinstaller --onefile --noconsole --icon=sunii.ico sunii.py
```

Then place `sunii.exe` anywhere and run it directly.

---

##  Startup (Optional)

To run at system boot:

1. Press `Win + R` → type `shell:startup`
2. Paste a shortcut to `sunii.exe` into that folder

---

##  License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.

---

##  Credits

- Built with `tkinter` + `pystray` + `WMI` + `Pillow`
- Designed by Nick/nkvsm • 2025
