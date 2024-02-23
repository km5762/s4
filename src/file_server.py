import hmac
import os
import pickle
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from socket import gethostbyname, gethostname
from typing import Any
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from Crypto.Cipher import AES

app = FastAPI()


PARENT_DIR = Path(__file__).parent
ROOT_DIR = PARENT_DIR / Path("root")

os.makedirs(ROOT_DIR, exist_ok=True)

load_dotenv()
name_server_url = os.environ.get("NAME_SERVER_URL")
API_KEY = os.environ.get("API_KEY")

if not name_server_url:
    exit("Error: NAME_SERVER environment variable is not set.")
if not API_KEY:
    exit("Error: API_KEY environment variable is not set.")

headers = {"Authorization": API_KEY}

journal = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global journal
    try:
        with open(f"{PARENT_DIR}{os.path.sep}journal.pk1", "rb") as file:
            journal = pickle.load(file)
    except OSError as e:
        print(e)
    await sync_changes()
    yield
    with open(f"{PARENT_DIR}{os.path.sep}journal.pk1", "wb") as file:
        pickle.dump(journal, file)


app = FastAPI(lifespan=lifespan)


class DirectoryItem(BaseModel):
    dir_name: str


def secure_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1.encode(), val2.encode())


@app.middleware("http")
async def check_authorization(request: Request, call_next):
    try:
        auth = request.headers["Authorization"]
    except KeyError:
        return JSONResponse(
            status_code=401, content={"error": "Authorization key not found"}
        )
    if not secure_compare(auth, API_KEY):
        return JSONResponse(
            status_code=403, content={"error": "Authorization key not found"}
        )
    response = await call_next(request)
    return response


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name) -> FileResponse:
    path = f"{ROOT_DIR.resolve()}{os.path.sep}{bucket_name}{os.path.sep}{object_name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Object not found")
    return FileResponse(
        path,
        filename=object_name,
    )


@app.get("/{bucket_name}")
def read_bucket(bucket_name) -> list[Any] | None:
    objects = ROOT_DIR / Path(bucket_name)
    if objects is None:
        raise HTTPException(status_code=404, detail="Bucket not found")

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
def create_bucket(directory_name: DirectoryItem, background_tasks: BackgroundTasks):
    dir_path = Path(directory_name.dir_name)
    target_dir_path = ROOT_DIR / dir_path
    try:
        journal[target_dir_path] = "UPLOADING"
        target_dir_path.mkdir()
        journal[target_dir_path] = "UPLOADED"
        background_tasks.add_task(sync_changes)
        return {"status": "ok", "message": f"Bucket made: {target_dir_path.resolve()}"}
    except FileExistsError as _:
        return {
            "status": "error",
            "message": f"Bucket already exists at {target_dir_path.resolve()}",
        }


@app.post("/{bucket_name}")
async def create_object(
    bucket_name, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    contents = await file.read()
    transferred_file_path = (
        f"{ROOT_DIR}{os.path.sep}{bucket_name}{os.path.sep}{file.filename}.enc"
    )

    if not Path(transferred_file_path).parent.exists():
        raise HTTPException(status_code=404, detail="Bucket not found")

    journal[transferred_file_path] = "UPLOADING"
    hasFileWriteErrored = False

    (ciphertext, nonce, hmac) = encrypt_file(contents, bytes.fromhex(API_KEY))

    try:
        with open(transferred_file_path, "wb") as f:
            f.write(hmac)
            f.write(nonce)
            f.write(ciphertext)
    except OSError:
        hasFileWriteErrored = True

    journal[transferred_file_path] = "UPLOADED"
    background_tasks.add_task(sync_changes)
    # TODO http error when bucketname doesnt exist
    if hasFileWriteErrored:
        return {"status": "error", "filename": f"{transferred_file_path}"}
    else:
        return {"status": "ok", "filename": f"{transferred_file_path}"}


@app.delete("/{bucket_name}")
def delete_bucket(bucket_name: str, background_tasks: BackgroundTasks):
    bucket_path = ROOT_DIR / Path(bucket_name)
    if not bucket_path.exists():
        raise HTTPException(status_code=404, detail="Bucket not found")

    try:
        journal[bucket_path] = "DELETING"
        bucket_path.rmdir()
        journal[bucket_path] = "DELETED"
        background_tasks.add_task(sync_changes)
        return {"status": "ok", "message": f"Bucket deleted: {bucket_path.resolve()}"}
    except OSError as e:
        return {"status": "error", "message": f"Error deleting bucket: {str(e)}"}


@app.delete("/{bucket_name}/{object_name}")
def delete_object(
    bucket_name: str, object_name: str, background_tasks: BackgroundTasks
):
    object_path = ROOT_DIR / Path(bucket_name) / Path(object_name)
    if not object_path.exists():
        raise HTTPException(status_code=404, detail="Object not found")

    try:
        journal[object_path] = "DELETING"
        object_path.unlink()
        journal[object_path] = "DELETED"
        background_tasks.add_task(sync_changes)
        return {"status": "ok", "message": f"Object deleted: {object_path.resolve()}"}
    except OSError as e:
        return {"status": "error", "message": f"Error deleting object: {str(e)}"}


async def sync_changes():
    response = httpx.get(name_server_url, headers=headers)
    file_servers = response.json()

    changes_to_remove = []
    # <path>: <status>
    for path in journal:
        all_servers_ok = True
        if journal[path] == "UPLOADED" or journal[path] == "DELETED":
            for file_server in file_servers:
                if file_server["host"] == gethostbyname(gethostname()):
                    continue
                if os.path.exists(path):
                    url = f"http://{file_server['host']}:{file_server['port']}/"
                    if os.path.isdir(path):
                        # head, tail = os.path.split(path)
                        bucket_name = Path(path).name
                        payload = {"dir_name": bucket_name}

                        if journal[path] == "DELETED":
                            r = httpx.delete(
                                url + os.path.sep + bucket_name, headers=headers
                            )
                            if r.status_code != 200:
                                all_servers_ok = False
                                break
                        else:
                            r = httpx.post(url, json=payload, headers=headers)
                            if r.status_code != 200:
                                all_servers_ok = False
                                break
                    else:
                        # del obj
                        file_path = Path(path)
                        bucket_path = file_path.parent

                        # # post to bucket to make sure it exists
                        # payload = {"dir_name": bucket_path.name}
                        # r = httpx.post(url, json=payload)
                        url += bucket_path.name

                        if journal[path] == "DELETED":
                            r = httpx.delete(
                                url + os.path.sep + file_path.name, headers=headers
                            )
                            if r.status_code != 200:
                                all_servers_ok = False
                                break
                        else:
                            # create obj
                            try:
                                with open(Path(path), "rb") as f:
                                    files = {"file": f}
                                    r = httpx.post(url, files=files, headers=headers)
                                    if r.status_code != 200:
                                        all_servers_ok = False
                                        break
                            except OSError as e:
                                print(e)
        if all_servers_ok:
            changes_to_remove.append(path)

    for path in changes_to_remove:
        del journal[path]


def encrypt_file(file_data, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, hmac = cipher.encrypt_and_digest(file_data)
    return (ciphertext, cipher.nonce, hmac)


def is_accessible_path(path: Path) -> bool:
    return ROOT_DIR < path
