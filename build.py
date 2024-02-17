import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

SRC_DIR = Path(f"{ROOT}{os.path.sep}src")
SCRIPTS_DIR = Path(f"{ROOT}{os.path.sep}src{os.path.sep}scripts")

OUT_DIR = Path("./out")
OUT_FILE_SERVER_DIR = Path(f"{ROOT}{os.path.sep}out{os.path.sep}file_server")
OUT_NAME_SERVER_DIR = Path(f"{ROOT}{os.path.sep}out{os.path.sep}name_server")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(OUT_FILE_SERVER_DIR, exist_ok=True)
os.makedirs(OUT_NAME_SERVER_DIR, exist_ok=True)

# Move files into out

if not SRC_DIR.exists():
    print("Could not find src folder")
    exit(1)
if not SCRIPTS_DIR.exists():
    print("Could not find src folder")
    exit(1)

for file in SRC_DIR.iterdir():
    if file.name == "file_server.py" or file.name == ".env":
        shutil.copy2(file.resolve(), OUT_FILE_SERVER_DIR.resolve())
    elif file.name == "name_server.py":
        shutil.copy2(file.resolve(), OUT_NAME_SERVER_DIR.resolve())
    elif file.name == "client.py":
        shutil.copy2(file.resolve(), OUT_DIR.resolve())

for file in SCRIPTS_DIR.iterdir():
    if file.name == "start_file_server.py":
        shutil.copy2(file.resolve(), OUT_FILE_SERVER_DIR.resolve())
    if file.name == "start_name_server.py":
        shutil.copy2(file.resolve(), OUT_NAME_SERVER_DIR.resolve())
