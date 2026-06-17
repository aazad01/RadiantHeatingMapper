# PyInstaller spec for the radiant-heat standalone executable.
# Build with:  pyinstaller radiant-heat.spec   (or ./build_executable.sh)
#
# matplotlib is intentionally excluded to keep the binary small and the build
# fast: the bundled executable targets the headless "compute"/"svg"/"serve"
# workflows. The interactive "show" command still works when run from a source
# checkout with matplotlib installed.

block_cipher = None

a = Analysis(
    ['src/cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['flask', 'numpy'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'PyQt5', 'PySide2', 'PIL', 'cryptography'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='radiant-heat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
)
