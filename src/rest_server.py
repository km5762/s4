from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return "HELLO"


@app.get("/{bucket_name}")
def read_bucket(bucket_name):
    return {"bucket_name": bucket_name}


@app.get("/{bucket_name}/{object_name}")
def read_object(bucket_name, object_name):
    return {"bucket_name": bucket_name, "object_name": object_name}
