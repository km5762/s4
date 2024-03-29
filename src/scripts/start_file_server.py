import uvicorn
import argparse
import httpx
import os
from socket import gethostname, gethostbyname
from dotenv import load_dotenv

DEFAULT_PORT = 8231


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the file server on the specified port."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port number to run the server on.",
    )
    args = parser.parse_args()
    return args.port


def advertise_to_name_server():
    load_dotenv()
    url = os.environ.get("NAME_SERVER_URL")
    if url:
        response = httpx.post(
            url, json={"host": gethostbyname(gethostname()), "port": DEFAULT_PORT}
        )
        if response.status_code not in [200, 409]:
            exit("Error: name server not available")
    else:
        exit("Error: NAME_SERVER environment variable is not set.")


if __name__ == "__main__":
    print(gethostbyname(gethostname()))
    port = parse_args()
    advertise_to_name_server()

    config = uvicorn.Config(
        "file_server:app", port=port, log_level="info", host="0.0.0.0"
    )
    server = uvicorn.Server(config)
    server.run()
