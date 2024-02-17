import httpx
import re
import time

REST_URL = "http://127.0.0.1:8000"

BUCKET_REGEX = re.compile(r"/\w+\/?$|\/$", re.I)
FILENAME_REGEX = re.compile(r'filename="(.+)"')
BANNED_CHARS_REGEX = re.compile(r"\/:*?\"<>\|")

def main() -> None:
    while user_input := input("Enter command: "):
        type = user_input.split(" ")[0]
        command = user_input.split(" ")[1:]
        match type:
            case "exit":
                exit(1)
            case "get" | "put" | "post" | "delete":
                handle_request(type, "".join(command))
            case _:
                print("Command not recognized")
                continue


def handle_request(type: str, command: str):
    if not verify_input(command):
        print("Invalid route.")
        return
    if command != "/":
        if command.endswith("/"):
            print(True)
            command = command[:-1]
    if BUCKET_REGEX.match(command):
        handle_dir(type, command)
    else:
        handle_object(type, command)


def handle_dir(type: str, command: str):
    r = httpx.request(type, f"{REST_URL}{command}")
    print(r.json())
    pass


def handle_object(type: str, command: str):
    r = httpx.request(type, f"{REST_URL}{command}")
    if r.status_code == 200:
        filename = filename_from_content_disposition(
            r.headers.get("Content-Disposition")
        )
        with open(filename, "wb") as f:
            f.write(r.content)
    else:
        print("Download failed")


def verify_input(command: str):
    return command.startswith("/")


def filename_from_content_disposition(content: str | None):
    if content is None:
        return time.time_ns()
    parts = content.split("; ")
    for part in parts:
        if part.startswith("filename="):
            filename = part.split("=")[1].strip('"')
            # TODO might have problems if returning more than one file
            return filename
    return time.time_ns()


if __name__ == "__main__":
    main()
