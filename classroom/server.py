#!/usr/bin/env python3
"""
Сервер классного монитора (веб-версия, прототип — базовая часть аналога Veyon).

Роль: один центральный компьютер/сервер.
  - раздаёт веб-консоль преподавателя (открывается в браузере, в т.ч. на телефоне);
  - принимает подключения агентов учеников (student_agent.py / StudentAgent.exe);
  - в реальном времени пересылает кадры экранов ученика -> преподавателю;
  - пересылает события управления (мышь/клавиатура) преподаватель -> ученику.

Доступ ограничен общим КЛАСС-КОДОМ, чтобы к экранам не подключился чужой
в той же сети. Это прозрачный мониторинг для своих/школьных машин с ведома
пользователей — не скрытая слежка.

Запуск как скрипт:
    pip install flask flask-socketio
    python server.py
Либо как собранный TeacherServer.exe — тогда ставить ничего не нужно,
браузер с консолью откроется сам.
"""

import os
import sys
import socket
import secrets
import string
import threading
import webbrowser

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room

# ---- Настройки ------------------------------------------------------------
# Класс-код не задаётся в коде (репозиторий публичный). При каждом запуске
# генерируется случайный код и показывается в окне сервера. Его и сообщаешь
# ученикам/вводишь в телефоне. Можно задать свой через переменную окружения
# CLASS_CODE.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # без похожих 0/O, 1/I
CLASS_CODE = os.environ.get("CLASS_CODE") or "".join(secrets.choice(_ALPHABET) for _ in range(6))
PORT = 8080


def resource_path(rel):
    """Путь к ресурсу, работает и из исходника, и из собранного .exe."""
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, rel)


app = Flask(__name__, template_folder=resource_path("templates"))
app.config['SECRET_KEY'] = 'classroom-monitor-prototype'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading',
                    max_http_buffer_size=25_000_000)

students = {}   # sid -> name


def students_list():
    return [{'sid': sid, 'name': name} for sid, name in students.items()]


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@app.route('/')
def index():
    return render_template('teacher.html')


# ---- Регистрация ----------------------------------------------------------
@socketio.on('register_teacher')
def on_register_teacher(data):
    if (data or {}).get('code') != CLASS_CODE:
        socketio.emit('denied', {'reason': 'Неверный класс-код'}, room=request.sid)
        return
    join_room('teachers')
    socketio.emit('student_list', students_list(), room=request.sid)


@socketio.on('register_student')
def on_register_student(data):
    data = data or {}
    if data.get('code') != CLASS_CODE:
        socketio.emit('denied', {'reason': 'Неверный класс-код'}, room=request.sid)
        return
    students[request.sid] = data.get('name', 'ученик')
    socketio.emit('student_list', students_list(), room='teachers')


# ---- Поток данных ---------------------------------------------------------
@socketio.on('frame')
def on_frame(data):
    if request.sid not in students:
        return
    socketio.emit('frame', {
        'sid': request.sid,
        'name': students[request.sid],
        'data': (data or {}).get('data'),
    }, room='teachers')


@socketio.on('control')
def on_control(data):
    target = (data or {}).get('target')
    if target:
        socketio.emit('control', data, room=target)


@socketio.on('message_all')
def on_message_all(data):
    text = (data or {}).get('text', '')
    socketio.emit('message', {'text': text}, room='students')


@socketio.on('join_students_room')
def on_join_students_room():
    join_room('students')


@socketio.on('disconnect')
def on_disconnect():
    if request.sid in students:
        students.pop(request.sid, None)
        socketio.emit('student_list', students_list(), room='teachers')


def open_browser():
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass


def main():
    ip = local_ip()
    print("=" * 60)
    print("  Сервер классного монитора запущен")
    print()
    print(f"      КЛАСС-КОД:  {CLASS_CODE}")
    print("      (его сообщи ученикам и впиши в телефоне)")
    print()
    print("  Адреса в одной локальной сети:")
    print(f"    на этом компьютере:         http://localhost:{PORT}")
    print(f"    телефон/другие устройства:  http://{ip}:{PORT}")
    print(f"    для агентов учеников:       {ip}:{PORT}")
    print()
    print("  Для учеников в другом городе — запускай через start_online.bat,")
    print("  он даст публичную ссылку https://...trycloudflare.com")
    print("  (окно можно свернуть; закрытие окна остановит сервер)")
    print("=" * 60)
    # открыть консоль в браузере автоматически (удобно в собранном .exe)
    threading.Timer(1.5, open_browser).start()
    socketio.run(app, host='0.0.0.0', port=PORT, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
