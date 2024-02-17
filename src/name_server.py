from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Annotated
import pickle
import os
from pathlib import Path

registries = []

ROOT = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    global registries
    try:
        with open(f"{ROOT}{os.path.sep}registries.pk1", "rb") as file:
            registries = pickle.load(file)
    except Exception as e:
        print(e)
    yield
    with open(f"{ROOT}{os.path.sep}registries.pk1", "wb") as file:
        pickle.dump(registries, file)


app = FastAPI(lifespan=lifespan)


class Registry(BaseModel):
    host: Annotated[
        str,
        Field(
            pattern=r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$"
        ),
    ]
    port: Annotated[int, Field(strict=True, ge=0, le=65535)]


@app.get("/")
def read_servers():
    return registries


@app.post("/")
def register_server(registry: Registry):
    for existing_registry in registries:
        if (
            existing_registry.host == registry.host
            and existing_registry.port == registry.port
        ):
            raise HTTPException(status_code=409, detail="Duplicate registry")
    registries.append(registry)
