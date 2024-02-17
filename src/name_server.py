from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Annotated

app = FastAPI()

registries = []


class Registry(BaseModel):
    host: Annotated[
        str,
        Field(
            pattern=r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$'
        ),
    ]
    port: Annotated[int, Field(strict=True, ge=0, le=65535)]


@app.get("/")
def read_servers():
    return registries


@app.post("/")
def register_server(registry: Registry):
    registries.append(registry)
