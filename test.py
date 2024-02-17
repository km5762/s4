import httpx

# server side key. stored and passed as env var
# print(get_random_bytes(32))
# we give client an api key. we compare digests when we receive a client request
# if digest is good, when we decrypt

# response = httpx.get("http://localhost:8232/")
response = httpx.post(
    "http://localhost:8232/", json={"host": "www.j.com", "port": 5}
)

print(response.status_code)
print(response.headers)
print(response.content)
# print(response.)
