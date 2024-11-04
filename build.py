import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_spec_file(script_name: str, icon_path: str = None) -> str:
    if platform.system() == "Windows":
        console_setting = "False"
    else:
        console_setting = "True"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{script_name}'],
    pathex=[],
    binaries=[],
    hiddenimports=[
        'tkinter',
        'requests',
        'psutil',
        'threading',
        'datetime',
        'queue',
        'pathlib'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{script_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_setting},
"""
    # Add icon path if provided
    if icon_path:
        spec_content += f"    icon='{icon_path}',\n"
    
    spec_content += f")"

    spec_file = f"{Path(script_name).stem}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    return spec_file

def build_executable(script_name: str, spec_file: str):
    subprocess.check_call([
            "pyinstaller",
            "--clean",
            "--onefile",
            spec_file
    ])

def main():
    os.chrdir(os.path.dirname(os.path.abspath(__file__)))

    print("Installing requirements...")
    install_requirements()

    scripts = ["bot_monitor.py", "installer_gui.py"]

    for script in scripts:
        print(f"Building {script}...")
        spec_file = create_spec_file(script)    # TODO: Add icon path

        try:
            build_executable(script, spec_file)
            print(f"Built {script} successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error building {script}: {e}")
            continue
    
        try:
            os.remove(spec_file)
        except:
            pass
    
    dist_dir = Path("dist")
    if dist_dir.exists():
        platform_dir = dist_dir / platform.system().lower()
        platform_dir.mkdir(exist_ok=True)

        for item in dist_dir.glob("*"):
            if item.is_file():
                shutil.move(str(item), str(platform_dir/item.name))

    print("Build complete!")
    print(f"Executable(s) can be found in {platform_dir}")

if __name__ == "__main__":
    main()