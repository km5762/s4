# SDS3 RESTful Storage: Super Duper Simple Storage Service (AWS S3 "Clone")

## Authors
**Carlos Medina** and **Myles Ku**  
*February 26, 2024*

---

## Overview
SDS3 is a RESTful file server designed to mimic key functionalities of Amazon S3. It provides a bucket-like flat file system with operations for reading, writing, and deleting files and buckets. Built with **Python**, **FastAPI**, and **uvicorn**, SDS3 includes both a RESTful server and a CLI client.

---

## Features

### File Server (`file_server.py`)
The RESTful file server supports the following routes:

- **GET /**  
  Returns a list of bucket names and metadata (creation time, size).

- **GET /<bucket_name>**  
  Returns a list of objects in the specified bucket, along with metadata.

- **GET /<bucket_name>/<object_name>**  
  Downloads the specified object.

- **POST /**  
  Creates a new bucket. Payload: `{ "bucket_name": "<name>" }`

- **POST /<bucket_name>/**  
  Uploads a file to the specified bucket. Payload: `{ "file": "<file>" }`

- **DELETE /<bucket_name>**  
  Deletes the specified bucket (must be empty).

- **DELETE /<bucket_name>/<object_name>**  
  Deletes the specified object in the bucket.

### Client (`client.py`)
A CLI tool to interact with the file server, supporting all the operations listed above.

### Utilities
- **`build.py`**: Organizes and structures source files into `/out`.
- **`start_file_server.py`**: Starts the file server on a specified port.

---

## Distributed Extensions

### Name Server (`name_server.py`)
We extended SDS3 to support a distributed network of file servers:
- **POST /**  
  Registers a server at the specified host and port. Payload: `{ "host": "<host>", "port": <port> }`

- **GET /**  
  Returns a list of registered file servers.

The name server persists its state using `registries.pkl` for serialization.

### Additional Utilities
- **`start_name_server.py`**: Launches the name server.
- **Synchronization**: A journaling mechanism ensures eventual consistency across file servers, even during crashes or restarts.

---

## Results
- **Core Features**: All REST routes function as expected, tested using a single file server and client.
- **Distributed Network**: Implemented multi-server synchronization with eventual consistency.
- **Encryption**: Files are encrypted at rest, similar to S3's storage model.
- **Authentication**: Access to the file server is protected by an API key.

---

## Challenges
1. **Debugging Distributed Systems**: Testing required coordinating multiple servers, deleting files manually, and verifying responses.
2. **Server Discovery**: Used environment variables for a fixed name server address, which is not ideal for scalability.
3. **Consistency in Multi-Master Replication**: Solved using journaling but faced issues with infinite loops, resolved by custom headers.

---

## Lessons Learned
- Designed and implemented a REST API with Python and FastAPI.
- Gained insights into distributed object storage and synchronization.
- Explored encryption, API key authorization, and edge deployment strategies.
