from fastapi import FastAPI
import os
from datetime import datetime
from pathlib import Path

app = FastAPI()


@app.get("/")
def read_root():
    root_path = os.getenv("ROOT")
    if root_path is None:
        root = Path("./root")
    else:
        root = Path(root_path)

    metadata = []
    for bucket in root.iterdir():
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
    bucket_names = os.listdir(bucket_name)

    metadata = []
    for bucket_name in bucket_names:
        bucket_size = Path(bucket_name).lstat().st_size
        # os.path.getsize(bucket_name)
        creation_time = Path(bucket_name).stat().st_ctime
        # os.path.getctime(bucket_name)
        created_at = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

        metadata.append(
            {
                "name": bucket_name,
                "size": bucket_size,
                "created_at": created_at,
            }
        )

    return metadata


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name):
    return {"bucket_name": bucket_name, "object_name": object_name}
