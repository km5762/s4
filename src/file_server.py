from typing import Any
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
from datetime import datetime
from pathlib import Path


app = FastAPI()


ROOT = Path("../root")

os.makedirs(ROOT, exist_ok=True)


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name) -> FileResponse:
    return FileResponse(
        f"{ROOT.resolve()}{os.path.sep}{bucket_name}{os.path.sep}{object_name}",
        filename=object_name,
    )


@app.get("/{bucket_name}")
def read_bucket(bucket_name) -> list[Any] | None:
    objects = ROOT / Path(bucket_name)
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


@app.post("/{bucket_name}")
def create_bucket(bucket_name):
    file = Path(f"{ROOT.resolve()}{os.path.sep}{bucket_name}")
    try:
        file.mkdir()
        return {"status": "ok", "message": f"Bucket made: {file.resolve()}"}
    except FileExistsError as _:
        return {
            "status": "error",
            "message": f"Bucket already exists at {file.resolve()}",
        }


@app.get("/")
def read_root() -> list[Any]:
    metadata = []
    for bucket in ROOT.iterdir():
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


def is_accessible_path(path: Path) -> bool:
    return ROOT < path
