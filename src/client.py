import httpx
REST_URL = "http://127.0.0.1:8000"


def main() -> None:
    while user_input := input("Enter command: "):
        type = user_input.split(" ")[0]
        command = user_input.split(" ")[1:]
        match type:
            case "exit":
                print("Exiting")
                exit(1)
            case "get" | "g":
                handle_get("".join(command))
            case "put":
                handle_post("".join(command))
            case "post" | "p":
                handle_put("".join(command))
            case "delete" | "del":
                handle_del("".join(command))
            case _:
                print("Command not recognized")
                continue


def handle_get(command: str):
    if not verify_input(command):
        print("Invalid route.")
        return
    r = httpx.get(f"{REST_URL}")
    print(r.json())


def handle_put(command: str):
    if not verify_input(command):
        print("Invalid route.")
        return
    r = httpx.put(f"{REST_URL}")
    print(r.json())


def handle_post(command: str):
    if not verify_input(command):
        print("Invalid route.")
        return
    r = httpx.post(f"{REST_URL}")
    print(r.json())


def handle_del(command: str):
    if not verify_input(command):
        print("Invalid route.")
        return
    r = httpx.delete(f"{REST_URL}")
    print(r.json())


def verify_input(command: str):
    return command.startswith("/")


if __name__ == "__main__":
    main()
