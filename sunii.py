import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import datetime
import os
import configparser
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import wmi
import pythoncom

CONFIG_FILE = "sunii_config.ini"
ICON_FILE = "sunii.ico"

DARK_BG = "#1e1e1e"
DARK_FG = "#ffffff"
LIGHT_BG = "#f0f0f0"
LIGHT_FG = "#000000"
GLASS_ALPHA = 0.95

class SuniiScheduler:
    def __init__(self, app_ref=None):
        self.running = False
        self.app_ref = app_ref

    def start(self, night_hour, night_minute, morning_hour, morning_minute, night_brightness, day_brightness):
        self.running = True
        threading.Thread(
            target=self.loop,
            args=(night_hour, night_minute, morning_hour, morning_minute, night_brightness, day_brightness),
            daemon=True
        ).start()

    def stop(self):
        self.running = False

    def loop(self, night_hour, night_minute, morning_hour, morning_minute, night_brightness, day_brightness):
        pythoncom.CoInitialize()
        while self.running:
            now = datetime.datetime.now()
            if self.app_ref and getattr(self.app_ref, 'override_until', None):
                if now < self.app_ref.override_until:
                    time.sleep(30)
                    continue
                else:
                    self.app_ref.override_until = None
            current_time = (now.hour, now.minute)
            night_time = (night_hour, night_minute)
            morning_time = (morning_hour, morning_minute)
            is_night = night_time <= current_time or current_time < morning_time

            if self.app_ref:
                self.app_ref.apply_theme(is_night)

            if is_night:
                set_brightness(night_brightness)
            else:
                set_brightness(day_brightness)
            time.sleep(30)

class App:
    def __init__(self, root, window):
        self.root = root
        self.window = window
        self.override_until = None
        self.scheduler = SuniiScheduler(self)
        self.theme = 'dark'
        self.config = load_config()

        self.night_hour = self.config.get('night_hour', "8")
        self.night_minute = self.config.get('night_minute', "0")
        self.night_ampm = self.config.get('night_ampm', 'PM')
        self.morning_hour = self.config.get('morning_hour', "7")
        self.morning_minute = self.config.get('morning_minute', "0")
        self.morning_ampm = self.config.get('morning_ampm', 'AM')

        self.setup_styles()
        self.build_ui()
        self.apply_theme(self.is_night_now())

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.apply_style_colors(DARK_BG, DARK_FG)

    def apply_style_colors(self, bg, fg):
        self.window.configure(bg=bg)
        self.window.attributes('-alpha', GLASS_ALPHA)

        style = self.style
        style.configure("TButton", background=bg, foreground=fg, borderwidth=1, focusthickness=0, focuscolor=bg, relief="flat")
        style.map("TButton", background=[("active", "#333333"), ("pressed", "#444444")], foreground=[("active", fg), ("pressed", fg)])
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TMenubutton", background=bg, foreground=fg, relief="flat")
        style.configure("TScale", background=bg, troughcolor="#444444", sliderthickness=14)

    def build_ui(self):
        self.window.title("sunii")

        if os.path.exists(ICON_FILE):
            try:
                self.window.iconbitmap(ICON_FILE)
            except Exception as e:
                print(f"Failed to set window icon: {e}")

        ttk.Label(self.window, text="Night Start (hour:min)").grid(row=0, column=0, pady=5)
        self.night_hour_entry = tk.Entry(self.window, width=5)
        self.night_hour_entry.insert(0, self.night_hour)
        self.night_hour_entry.grid(row=0, column=1)
        self.night_minute_entry = tk.Entry(self.window, width=5)
        self.night_minute_entry.insert(0, self.night_minute)
        self.night_minute_entry.grid(row=0, column=2)
        self.night_ampm_var = tk.StringVar(value=self.night_ampm)
        ttk.OptionMenu(self.window, self.night_ampm_var, self.night_ampm_var.get(), "AM", "PM").grid(row=0, column=3)

        ttk.Label(self.window, text="Morning Start (hour:min)").grid(row=1, column=0, pady=5)
        self.morning_hour_entry = tk.Entry(self.window, width=5)
        self.morning_hour_entry.insert(0, self.morning_hour)
        self.morning_hour_entry.grid(row=1, column=1)
        self.morning_minute_entry = tk.Entry(self.window, width=5)
        self.morning_minute_entry.insert(0, self.morning_minute)
        self.morning_minute_entry.grid(row=1, column=2)
        self.morning_ampm_var = tk.StringVar(value=self.morning_ampm)
        ttk.OptionMenu(self.window, self.morning_ampm_var, self.morning_ampm_var.get(), "AM", "PM").grid(row=1, column=3)

        ttk.Label(self.window, text="Night Brightness").grid(row=2, column=0, pady=5)
        self.night_brightness = ttk.Scale(self.window, from_=0, to=100, orient="horizontal")
        self.night_brightness.set(float(self.config.get('night_brightness', "30")))
        self.night_brightness.grid(row=2, column=1, columnspan=3, sticky="we", padx=5)

        ttk.Label(self.window, text="Day Brightness").grid(row=3, column=0, pady=5)
        self.day_brightness = ttk.Scale(self.window, from_=0, to=100, orient="horizontal")
        self.day_brightness.set(float(self.config.get('day_brightness', "100")))
        self.day_brightness.grid(row=3, column=1, columnspan=3, sticky="we", padx=5)

        frame_buttons = ttk.Frame(self.window)
        frame_buttons.grid(row=4, column=0, columnspan=4, pady=(10, 15))
        ttk.Button(frame_buttons, text="Start sunii", command=self.run_scheduler).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Stop sunii", command=self.stop_scheduler).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Save Settings", command=self.save_settings).pack(side="left", padx=10)

        self.night_brightness.bind("<ButtonRelease-1>", self.apply_current_brightness)
        self.day_brightness.bind("<ButtonRelease-1>", self.apply_current_brightness)

        self.window.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def run_scheduler(self):
        self.scheduler.start(
            self.convert_to_24h(self.night_hour_entry.get(), self.night_ampm_var.get()),
            int(self.night_minute_entry.get()),
            self.convert_to_24h(self.morning_hour_entry.get(), self.morning_ampm_var.get()),
            int(self.morning_minute_entry.get()),
            self.night_brightness.get(),
            self.day_brightness.get()
        )

    def stop_scheduler(self):
        self.scheduler.stop()

    def minimize_to_tray(self):
        self.window.withdraw()
        image = self.create_image()
        menu = pystray.Menu(
            item('Restore', self.restore_window, default=True),
            item('Exit', self.exit_app)
        )
        self.tray_icon = pystray.Icon("sunii", image, "sunii", menu)
        self.tray_icon.run_detached()

    def create_image(self):
        image = Image.new('RGB', (64, 64), color=(25, 25, 50))
        d = ImageDraw.Draw(image)
        d.ellipse((10, 10, 30, 30), fill=(255, 215, 0))
        d.ellipse((34, 10, 54, 30), fill=(180, 100, 255))
        return image

    def restore_window(self, icon, item):
        self.tray_icon.stop()
        self.window.deiconify()

    def exit_app(self, icon, item):
        self.tray_icon.stop()
        self.window.quit()

    def apply_theme(self, is_night):
        self.window.title(f"sunii ({'night' if is_night else 'day'})")
        if is_night:
            self.apply_style_colors(DARK_BG, DARK_FG)
            self.theme = 'dark'
        else:
            self.apply_style_colors(LIGHT_BG, LIGHT_FG)
            self.theme = 'light'

    def convert_to_24h(self, hour, ampm):
        hour = int(hour)
        if ampm == 'PM' and hour != 12:
            hour += 12
        if ampm == 'AM' and hour == 12:
            hour = 0
        return hour

    def is_night_now(self):
        now = datetime.datetime.now()
        current = (now.hour, now.minute)
        night = (self.convert_to_24h(self.night_hour_entry.get(), self.night_ampm_var.get()), int(self.night_minute_entry.get()))
        morning = (self.convert_to_24h(self.morning_hour_entry.get(), self.morning_ampm_var.get()), int(self.morning_minute_entry.get()))
        return night <= current or current < morning

    def apply_current_brightness(self, event=None):
        self.override_until = datetime.datetime.now() + datetime.timedelta(minutes=5)
        if self.is_night_now():
            set_brightness(self.night_brightness.get())
        else:
            set_brightness(self.day_brightness.get())

    def save_settings(self):
        save_config({
            'night_hour': self.night_hour_entry.get(),
            'night_minute': self.night_minute_entry.get(),
            'night_ampm': self.night_ampm_var.get(),
            'morning_hour': self.morning_hour_entry.get(),
            'morning_minute': self.morning_minute_entry.get(),
            'morning_ampm': self.morning_ampm_var.get(),
            'night_brightness': str(int(round(self.night_brightness.get()))),
            'day_brightness': str(int(round(self.day_brightness.get())))
        })
        messagebox.showinfo("sunii", "Settings saved successfully.")

def set_brightness(level):
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI(namespace='wmi')
        methods = c.WmiMonitorBrightnessMethods()
        for method in methods:
            method.WmiSetBrightness(int(level), 0)
    except Exception as e:
        print(f"Brightness setting failed: {e}")

def save_config(data):
    config = configparser.ConfigParser()
    config['sunii'] = data
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['sunii'] = {
            'night_hour': "8", 'night_minute': "0", 'night_ampm': "PM",
            'morning_hour': "7", 'morning_minute': "0", 'morning_ampm': "AM",
            'night_brightness': "30", 'day_brightness': "100"
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config['sunii']

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    window = tk.Toplevel()
    app = App(root, window)
    window.mainloop()
