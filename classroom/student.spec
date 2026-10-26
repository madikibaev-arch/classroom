# -*- mode: python ; coding: utf-8 -*-
# Сборка агента ученика в один файл StudentAgent.exe
# Запуск:  pyinstaller --clean -y student.spec

from PyInstaller.utils.hooks import collect_submodules

# python-socketio / engineio грузят транспорты динамически — собираем их явно,
# иначе в .exe может не попасть модуль связи и агент не подключится.
hidden = (
    collect_submodules('engineio')
    + collect_submodules('socketio')
    + ['websocket', 'requests', 'engineio.async_drivers.threading']
)

a = Analysis(
    ['student_agent.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
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
    name='StudentAgent',
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
)
