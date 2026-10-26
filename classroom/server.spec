# -*- mode: python ; coding: utf-8 -*-
# Сборка сервера преподавателя в один файл TeacherServer.exe
# Запуск:  pyinstaller --clean -y server.spec

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('templates/teacher.html', 'templates')],
    hiddenimports=['engineio.async_drivers.threading'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TeacherServer',
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,          # окно-консоль показывает адрес и класс-код
)
