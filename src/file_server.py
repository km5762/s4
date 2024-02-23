from typing import Any
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager
import pickle


app = FastAPI()


PARENT_DIR = Path(__file__).parent
ROOT_DIR = PARENT_DIR / Path("root")

os.makedirs(ROOT_DIR, exist_ok=True)

load_dotenv()
name_server_url = os.environ.get("NAME_SERVER_URL")

if not name_server_url:
    exit("Error: NAME_SERVER environment variable is not set.")

journal = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global journal
    try:
        with open(f"{PARENT_DIR}{os.path.sep}journal.pk1", "rb") as file:
            journal = pickle.load(file)
    except OSError as e:
        print(e)
    sync_changes()
    yield
    with open(f"{PARENT_DIR}{os.path.sep}journal.pk1", "wb") as file:
        pickle.dump(journal, file)


app = FastAPI(lifespan=lifespan)


class DirectoryItem(BaseModel):
    dir_name: str


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name) -> FileResponse:
    return FileResponse(
        f"{ROOT_DIR.resolve()}{os.path.sep}{bucket_name}{os.path.sep}{object_name}",
        filename=object_name,
    )


@app.get("/{bucket_name}")
def read_bucket(bucket_name) -> list[Any] | None:
    objects = ROOT_DIR / Path(bucket_name)
    if objects is None:
        # bucket doesnt exist
        return None

    objects = objects.iterdir()

    metadata = []
    for object in objects:
        object_size = object.lstat().st_size
        creation_time = object.stat().st_ctime
        created_at = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

        metadata.append(
            {
                "name": object,
                "size": object_size,
                "created_at": created_at,
            }
        )

    return metadata


@app.get("/")
def read_root() -> list[Any]:
    metadata = []
    for bucket in ROOT_DIR.iterdir():
        bucket_size = bucket.lstat().st_size
        creation_time = bucket.stat().st_ctime
        created_at = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

        metadata.append(
            {
                "name": bucket.name,
                "size": bucket_size,
                "created_at": created_at,
            }
        )

    return metadata


@app.post("/")
def create_bucket(directory_name: DirectoryItem):
    dir_path = Path(directory_name.dir_name)
    target_dir_path = ROOT_DIR / dir_path
    try:
        journal[target_dir_path] = "UPLOADING"
        target_dir_path.mkdir()
        journal[target_dir_path] = "UPLOADED"
        sync_changes()
        return {"status": "ok", "message": f"Bucket made: {target_dir_path.resolve()}"}
    except FileExistsError as _:
        return {
            "status": "error",
            "message": f"Bucket already exists at {target_dir_path.resolve()}",
        }


@app.post("/{bucket_name}")
async def create_object(bucket_name, file: UploadFile = File(...)):
    contents = await file.read()
    transferred_file_path = (
        f"{ROOT_DIR}{os.path.sep}{bucket_name}{os.path.sep}{file.filename}"
    )

    journal[transferred_file_path] = "UPLOADING"
    hasFileWriteErrored = False

    try:
        with open(transferred_file_path, "wb") as f:
            f.write(contents)
    except OSError:
        hasFileWriteErrored = True

    journal[transferred_file_path] = "UPLOADED"
    sync_changes()

    if hasFileWriteErrored:
        return {"status": "error", "filename": f"{transferred_file_path}"}
    else:
        return {"status": "ok", "filename": f"{transferred_file_path}"}


def sync_changes():
    response = httpx.get(name_server_url)
    file_servers = response.json()

    changes_to_remove = []
    allServersResponded = True
    # <path>: <status>
    for path in journal:
        if journal[path] == "UPLOADED":
            for file_server in file_servers:
                if os.path.exists(path):
                    url = f"http://{file_server['host']}:{file_server['port']}/"
                    if os.path.isdir(path):
                        # head, tail = os.path.split(path)
                        payload = {"dir_name": Path(path).name}
                        httpx.post(url, json=payload)
                    else:
                        file_path = Path(path)
                        bucket_path = file_path.parent

                        # post to bucket to make sure it exists
                        payload = {"dir_name": bucket_path.name}
                        r = httpx.post(url, json=payload)
                        if r.status_code == 200:
                            url += bucket_path.name
                            try:
                                with open(Path(path), "rb") as f:
                                    files = {"file": f}
                                    httpx.post(url, files=files)
                            except OSError as e:
                                print(e)
                        else:
                            allServersResponded = False
        if allServersResponded:
            changes_to_remove.append(path)

    for path in changes_to_remove:
        del journal[path]


def is_accessible_path(path: Path) -> bool:
    return ROOT_DIR < path
