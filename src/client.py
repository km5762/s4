import argparse
import re
import time
from pathlib import Path

import httpx

REST_URL = "http://127.0.0.1:8231"

BUCKET_REGEX = re.compile(r"/\w+\/?$|\/$", re.I)
FILENAME_REGEX = re.compile(r'filename="(.+)"')
BANNED_CHARS_REGEX = re.compile(r"\/:*?\"<>\|")

PARENT_DIR = Path(__file__).parent
headers = {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Script that requires an API key.")
    parser.add_argument("--api_key", type=str, help="API key")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key is required.")
        exit(1)
    global headers
    headers = {"Authorization": args.api_key}

    while user_input := input("Enter command: "):
        # get /
        # post / test_dir
        # post /testdir ./test_upload.pdf
        type = user_input.split(" ")[0]
        match type:
            case "exit":
                exit(1)
            case "get":
                try:
                    server_side_path = user_input.split(" ")[1]
                except IndexError:
                    print("Not enough arguments")
                    continue
                handle_get("".join(server_side_path))
            case "post":
                try:
                    server_side_path = user_input.split(" ")[1]
                    local_path = user_input.split(" ")[2]
                except IndexError:
                    print("Not enough arguments")
                    continue
                handle_post("".join(server_side_path), "".join(local_path))
            case "delete":
                try:
                    server_side_path = user_input.split(" ")[1]
                except IndexError:
                    print("Not enough arguments")
                    continue
                handle_del("".join(server_side_path))
            case _:
                print("Command not recognized")
                continue


def handle_get(server_side_path: str):
    if BUCKET_REGEX.match(server_side_path):
        res = get_dir(server_side_path)
    else:
        res = get_obj(server_side_path)
    print(res)


def handle_post(server_side_path: str, local_path: str):
    if server_side_path == "/":
        res = post_dir(server_side_path, local_path)
        print(res)
    else:
        res = post_obj(server_side_path, local_path)
        print(res)


def post_dir(server_side_path, local_path):
    url = f"{REST_URL}{server_side_path}"
    req = {"dir_name": local_path}
    r = httpx.post(url, json=req, headers=headers)
    return r.content


def post_obj(server_side_path: str, local_path: str):
    url = f"{REST_URL}{server_side_path}"
    with open(local_path, "rb") as f:
        files = {"file": f}
        r = httpx.post(url, files=files, headers=headers)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type")
            if "application/json" in content_type:
                return r.json()
            else:
                return r.content
        else:
            return "Error with sending object"


def handle_del(command: str):
    pass


def get_dir(command: str):
    r = httpx.get(f"{REST_URL}{command}", headers=headers)
    return r.json()


def get_obj(command: str):
    r = httpx.get(f"{REST_URL}{command}", headers=headers)
    if r.status_code == 200:
        filename = filename_from_content_disposition(
            r.headers.get("Content-Disposition")
        )
        file_path = PARENT_DIR / Path(filename)
        with open(file_path, "wb") as f:
            f.write(r.content)
        return f"Wrote {file_path}"
    else:
        return f"Download failed with status code {r.status_code}"


def verify_input(command: str):
    return command.startswith("/")


def filename_from_content_disposition(content: str | None):
    if content is None:
        return str(time.time_ns())
    parts = content.split("; ")
    for part in parts:
        if part.startswith("filename="):
            filename = part.split("=")[1].strip('"')
            # TODO might have problems if returning more than one file
            return filename
    return str(time.time_ns())


if __name__ == "__main__":
    main()
