import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config("name_server:app", port=8232, log_level="info")
    server = uvicorn.Server(config)
    server.run()
