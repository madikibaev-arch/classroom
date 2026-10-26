# -*- mode: python ; coding: utf-8 -*-
# Сборка агента ученика в один файл StudentAgent.exe
# Запуск:  pyinstaller --clean -y student.spec

a = Analysis(
    ['student_agent.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'engineio.async_drivers.threading',
    ],
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
    console=False,         # без чёрного окна; видно только окно согласия агента
)
