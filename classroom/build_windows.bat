@echo off
chcp 65001 >nul
REM ============================================================
REM  Сборка .exe для Windows. Запускается на любом Windows-ПК,
REM  где установлен Python 3.9+ (https://www.python.org/downloads/,
REM  при установке отметьте "Add Python to PATH").
REM  Двойной клик по этому файлу -> через пару минут готовые .exe
REM  появятся в папке dist.
REM ============================================================

echo [1/4] Обновляю pip...
python -m pip install --upgrade pip

echo [2/4] Ставлю зависимости...
python -m pip install pyinstaller flask flask-socketio "python-socketio[client]" mss pillow pyautogui

echo [3/4] Собираю сервер преподавателя (TeacherServer.exe)...
python -m PyInstaller --clean -y server.spec

echo [4/4] Собираю агент ученика (StudentAgent.exe)...
python -m PyInstaller --clean -y student.spec

echo.
echo ============================================================
echo  Готово! Файлы здесь:
echo    dist\TeacherServer.exe   - запускает учитель (один раз, на сервере)
echo    dist\StudentAgent.exe    - запускается на каждом компьютере ученика
echo ============================================================
pause
