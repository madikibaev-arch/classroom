#!/usr/bin/env python3
"""
Агент ученика (веб-версия, видимый, с согласием пользователя).

Подключается к серверу класса, передаёт свой экран в реальном времени и
принимает управление от преподавателя (движение курсора, клики, текст).

Прозрачность:
  - постоянно показывает окно "ваш экран виден преподавателю";
  - когда преподаватель управляет — загорается красный баннер;
  - кнопка "Запретить управление" мгновенно отключает приём управления
    (просмотр при этом можно оставить);
  - кнопка закрытия окна полностью останавливает агент.

Ставьте только на свои или школьные машины и только с ведома пользователя.

Запуск:
    pip install "python-socketio[client]" mss pillow pyautogui
    python student_agent.py <адрес-сервера> <класс-код> <имя>
    например:  python student_agent.py 192.168.1.10:8080 1234 Айдана
Без аргументов агент спросит адрес, код и имя.
"""

import io
import sys
import base64
import socket as pysocket
import threading
import time
import tkinter as tk
from tkinter import simpledialog, messagebox

import socketio
import mss
from PIL import Image

# управление вводом — необязательная часть; без него работает только просмотр
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    CONTROL_AVAILABLE = True
except Exception:
    CONTROL_AVAILABLE = False

FPS = 2
MAX_WIDTH = 1000
JPEG_QUALITY = 55

KEYMAP = {
    'Enter': 'enter', 'Backspace': 'backspace', 'Tab': 'tab', 'Escape': 'esc',
    'ArrowUp': 'up', 'ArrowDown': 'down', 'ArrowLeft': 'left', 'ArrowRight': 'right',
    'Delete': 'delete', 'Home': 'home', 'End': 'end',
}

sio = socketio.Client(reconnection=True, reconnection_delay=3)


class AgentUI:
    def __init__(self, root, server, code, name):
        self.root = root
        self.server = server
        self.code = code
        self.name = name
        self.running = True
        self.control_allowed = True
        self.screen_w, self.screen_h = 0, 0
        self._banner_until = 0

        root.title("Классный монитор — агент")
        root.geometry("440x240")
        root.attributes("-topmost", True)

        tk.Label(root, text="Ваш экран виден преподавателю",
                 font=("Arial", 13, "bold"), fg="#b00").pack(pady=(14, 4))
        self.status = tk.Label(root, text="Подключение…", fg="#555")
        self.status.pack()
        self.banner = tk.Label(root, text="", font=("Arial", 12, "bold"))
        self.banner.pack(pady=4)
        tk.Label(root, text=f"Сервер: {server}   Имя: {name}", fg="#555").pack()

        self.ctrl_btn = tk.Button(root, text="Запретить управление", command=self.toggle_control)
        self.ctrl_btn.pack(pady=6)
        if not CONTROL_AVAILABLE:
            self.ctrl_btn.configure(state="disabled", text="Управление недоступно (нет pyautogui)")
        tk.Button(root, text="Остановить и выйти", command=self.stop).pack(pady=2)

        root.protocol("WM_DELETE_WINDOW", self.stop)
        self.tick_ui()

    def set_status(self, text, color="#555"):
        self.root.after(0, lambda: self.status.configure(text=text, fg=color))

    def flash_control(self):
        self._banner_until = time.time() + 1.2

    def tick_ui(self):
        if not self.running:
            return
        active = time.time() < self._banner_until and self.control_allowed
        self.banner.configure(
            text="● ПРЕПОДАВАТЕЛЬ УПРАВЛЯЕТ ЭКРАНОМ" if active else "",
            fg="#c00")
        self.root.after(300, self.tick_ui)

    def toggle_control(self):
        self.control_allowed = not self.control_allowed
        self.ctrl_btn.configure(
            text="Запретить управление" if self.control_allowed else "Разрешить управление")

    def stop(self):
        self.running = False
        try:
            sio.disconnect()
        except Exception:
            pass
        self.root.destroy()

    def show_message(self, text):
        self.root.after(0, lambda: messagebox.showinfo("Сообщение от преподавателя", text))


ui = None  # заполняется в main


# ---- события сервера ------------------------------------------------------
@sio.event
def connect():
    sio.emit('register_student', {'code': ui.code, 'name': ui.name})
    sio.emit('join_students_room')
    ui.set_status("Подключено — экран передаётся", "#0a0")


@sio.event
def disconnect():
    if ui and ui.running:
        ui.set_status("Нет связи с сервером, переподключение…", "#b60")


@sio.on('denied')
def on_denied(data):
    ui.set_status("Отказано: " + data.get('reason', ''), "#b00")


@sio.on('message')
def on_message(data):
    ui.show_message(data.get('text', ''))


@sio.on('control')
def on_control(data):
    if not (CONTROL_AVAILABLE and ui and ui.control_allowed):
        return
    t = data.get('type')
    try:
        if t == 'move':
            pyautogui.moveTo(data['x'] * ui.screen_w, data['y'] * ui.screen_h, _pause=False)
            ui.flash_control()
        elif t == 'click':
            pyautogui.click(data['x'] * ui.screen_w, data['y'] * ui.screen_h, _pause=False)
            ui.flash_control()
        elif t == 'key':
            key = data.get('key', '')
            if key in KEYMAP:
                pyautogui.press(KEYMAP[key])
            elif len(key) == 1:
                pyautogui.typewrite(key)
            ui.flash_control()
    except Exception:
        pass


# ---- поток захвата экрана -------------------------------------------------
def capture_loop():
    while ui.running:
        if not sio.connected:
            time.sleep(1)
            continue
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                ui.screen_w, ui.screen_h = monitor['width'], monitor['height']
                interval = 1.0 / FPS
                while ui.running and sio.connected:
                    shot = sct.grab(monitor)
                    img = Image.frombytes("RGB", shot.size, shot.rgb)
                    if img.width > MAX_WIDTH:
                        h = int(img.height * MAX_WIDTH / img.width)
                        img = img.resize((MAX_WIDTH, h))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
                    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
                    sio.emit('frame', {'data': b64})
                    time.sleep(interval)
        except Exception:
            time.sleep(1)


def net_loop():
    url = ui.server
    if not url.startswith('http'):
        url = 'http://' + url
    while ui.running:
        try:
            if not sio.connected:
                sio.connect(url, wait_timeout=5)
            time.sleep(1)
        except Exception:
            ui.set_status("Не удаётся подключиться, повтор…", "#b60")
            time.sleep(3)


def main():
    global ui
    server = sys.argv[1] if len(sys.argv) > 1 else None
    code = sys.argv[2] if len(sys.argv) > 2 else None
    name = sys.argv[3] if len(sys.argv) > 3 else pysocket.gethostname()

    root = tk.Tk()
    root.withdraw()
    if not server:
        server = simpledialog.askstring("Подключение", "Адрес сервера (IP:порт):", parent=root)
    if not code:
        code = simpledialog.askstring("Подключение", "Класс-код:", parent=root)
    if not server or not code:
        root.destroy()
        return
    root.deiconify()

    ui = AgentUI(root, server.strip(), code.strip(), name)
    threading.Thread(target=net_loop, daemon=True).start()
    threading.Thread(target=capture_loop, daemon=True).start()
    root.mainloop()


if __name__ == '__main__':
    main()
