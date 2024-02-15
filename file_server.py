from fastapi import FastAPI
import os
from datetime import datetime
from pathlib import Path

app = FastAPI()

root_path = os.getenv("ROOT")
if root_path is None:
    ROOT = Path("./root")
else:
    ROOT = Path(root_path)


@app.get("/")
def read_root():
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


@app.get("/{bucket_name}")
def read_bucket(bucket_name):
    objects = Path(bucket_name)
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
                "bucket_name" : bucket_name,
                "name": object,
                "size": object_size,
                "created_at": created_at,
            }
        )

    return metadata


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name):
    object = Path(bucket_name / object_name)
    if object is None:
        return None
    
    object_size = object.lstat().st_size
    creation_time = object.stat().st_ctime
    created_at = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")
    return {"bucket_name": bucket_name, "name": object_name, "size" : object_size, "created_at":created_at, "blob": None}


def accessible_path(path: Path):
    return ROOT < path
