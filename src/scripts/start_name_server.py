import uvicorn
from socket import gethostbyname, gethostname

# host = gethostbyname(gethostname())
# print(f"hosting on {host}")
if __name__ == "__main__":
    config = uvicorn.Config("name_server:app", port=8232, log_level="info", host="0.0.0.0")
    server = uvicorn.Server(config)
    server.run()
