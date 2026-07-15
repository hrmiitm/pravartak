---
marp: true
---

# Docker

---

# The World Before Docker

A new teammate joins your project.

They clone the repository.

Now they need to:

* Install Python
* Install the correct Python version
* Install project dependencies
* Install databases and other services
* Configure every service
* Fix OS-specific issues

Hours later... The application finally runs. Maybe.

---

# The Classic Problem

> "But it works on my machine."

Your machine:

```text
Python 3.x
Specific dependencies
Database configured
Environment configured
```

Your teammate's machine:

```text
Different Python version
Different dependency versions
Different OS
Different configuration
```

Same code. Different environments. Different results.

---

# Docker Changes the Workflow

## Before Docker

```text
Clone Repository
      ↓
Install Runtime
      ↓
Install Dependencies
      ↓
Install Services
      ↓
Configure Everything
      ↓
Fix Environment Issues
      ↓
Run Application
```

## With Docker

```bash
git clone <repository>

docker compose up
```

Application is running.

---

# The Same Problem Exists in Deployment

Without containers, deploying to a server means:

* Install the runtime
* Install dependencies
* Install required services
* Configure the environment
* Resolve server-specific issues
* Start the application

What if we could package the application environment?

---

# Enter Containers

A container packages:

* Application code
* Runtime
* Dependencies
* Required configuration

into an isolated environment.

> Package the application and its environment together.

---

# What is Docker?

Docker is a platform that makes working with containers easy.

It provides tools to:

* Build container images
* Run containers
* Manage containers
* Share images

Docker did not invent the fundamental idea of containers.

It made containers accessible and easy to use.

---

# Two Fundamental Concepts

## Image

A static, packaged artifact.

It contains everything required to run an application.

```text
Application Code
Runtime
Dependencies
Configuration
```

Think of an image as a **blueprint**.

---

# Container

A container is a **running instance of an image**.

```text
Docker Image
     ↓
 docker run
     ↓
Running Container
```

An image is static.

A container is alive and running.

---

# Image vs Container

```text
IMAGE                    CONTAINER

Blueprint       →        Running Instance

Static                   Running

Stored                   Executes Processes

Reusable                 Created from Image
```

One image can create multiple containers.

---

# Containers are Isolated

Each container has its own isolated environment.

```text
HOST MACHINE

┌─────────────────┐
│   Container A   │
│   Python App    │
│   Dependencies  │
└─────────────────┘

┌─────────────────┐
│   Container B   │
│    Database     │
└─────────────────┘
```

Applications no longer need to install every dependency directly on the host.

---

# Where Do Images Live?

Images can be stored in container registries.

A registry is a repository for container images.

One popular public registry is Docker Hub.

```text
Docker Hub
     ↓
docker pull
     ↓
Local Machine
     ↓
docker run
     ↓
Container
```

---

# Stage 1: Using Existing Images

We don't always need to build an image.

We can use an existing image.

```bash
docker pull nginx
```

Run it:

```bash
docker run -p 8080:80 nginx
```

Open:

```text
localhost:8080
```

We now have a web server running without installing nginx.

---

# Talking to a Container

Imagine our application runs on port `8000` inside the container.

The application is isolated.

We expose it to our host machine using port mapping.

```text
HOST                    CONTAINER

localhost:8000  ──────>  8000
```

```bash
docker run -p 8000:8000 my-app
```

Format:

```text
HOST_PORT:CONTAINER_PORT
```

---

# Stage 2: Building Our Own Image

So far, we used images created by someone else.

Now we have our own application.

How do we package it?

Using a:

# Dockerfile

---

# What is a Dockerfile?

A Dockerfile contains instructions for building an image.

```text
Dockerfile
     ↓
docker build
     ↓
Docker Image
     ↓
docker run
     ↓
Container
```

---

# Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV APP_ENV=production

CMD ["python", "app.py"]
```

Let's understand each instruction.

---

# FROM

```dockerfile
FROM python:3.12-slim
```

Defines the base image.

We do not need to manually install Python.

Our image starts from an existing Python image.

```text
Python Base Image
       +
Our Application
       =
Our Image
```

---

# COPY

```dockerfile
COPY . .
```

Copies files from our host machine into the image.

```text
Our Project Folder
        ↓
Container Image
```

---

# RUN

```dockerfile
RUN pip install -r requirements.txt
```

Runs a command while building the image.

Commonly used to:

* Install dependencies
* Install packages
* Prepare the application

---

# ENV

```dockerfile
ENV APP_ENV=production
```

Defines an environment variable.

The application can access this variable inside the container.

---

# CMD

```dockerfile
CMD ["python", "app.py"]
```

Defines the default command executed when the container starts.

```text
Container Starts
       ↓
python app.py
       ↓
Application Runs
```

---

# Building Our Image

```bash
docker build -t my-app .
```

```text
Dockerfile
     ↓
BUILD
     ↓
my-app Image
```

Run it:

```bash
docker run -p 8000:8000 my-app
```

---

# Sharing Our Image

Our teammate should not need to rebuild everything.

We can push our image to a registry.

```text
Our Machine
     ↓
Docker Image
     ↓
Docker Hub
     ↓
Teammate's Machine
```

Push:

```bash
docker push username/my-app
```

Teammate:

```bash
docker pull username/my-app

docker run username/my-app
```

Same packaged application.

Different machine.

---

# But What About Data?

Imagine running a database inside a container.

```text
Container
┌─────────────────────┐
│      Database       │
│                     │
│ users.db             │
└─────────────────────┘
```

We remove the container.

```bash
docker rm database
```

What happens to the data?

---

# Containers are Ephemeral

Container filesystems should not be treated as permanent storage.

Remove the container...

and container-local data is removed with it.

This is a major problem for:

* Databases
* Uploaded files
* Stateful applications

We need persistent storage.

---

# Docker Volumes

A volume stores data outside the container's writable layer.

```text
CONTAINER                 HOST

/database/data  ──────>   Docker Volume
```

The container can be removed.

The volume remains.

A new container can reuse the same volume.


---

# Why Volumes Matter

```text
Container 1
     ↓
Writes Data
     ↓
Docker Volume
```

Remove Container 1.

```text
Docker Volume
     ↑
Container 2
```

Container 2 can access the same data.

The application is replaceable.

The data persists.

---

# Stage 3: Multiple Containers

Real applications rarely contain one service.

Imagine:

```text
Web Application

Database

Cache
```

We could run each manually.

```bash
docker run ...
docker run ...
docker run ...
```

And configure networking, ports, and volumes ourselves. Or...

---

# Docker Compose

Docker Compose lets us define multiple containers in one file.

```text
compose.yaml
```

It describes:

* Services
* Images
* Ports
* Volumes
* Environment variables

---

# compose.yaml

```yaml
services:

  app:
    build: .
    ports:
      - "8000:8000"

  database:
    image: postgres
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

Our entire application stack is now defined as configuration.

---

# Running the Entire Application

```bash
docker compose up
```

```text
compose.yaml
      ↓
┌─────────────────┐
│ App Container   │
└─────────────────┘
         ↓
┌─────────────────┐
│ Database        │
└─────────────────┘
         ↓
┌─────────────────┐
│ Persistent Vol  │
└─────────────────┘
```

One command for entire application stack.

---

# Docker vs Podman

Docker and Podman solve largely the same problem.

Both can:

* Build images
* Run containers
* Manage containers
* Use container registries

The major architectural difference is how they manage containers.

---

# Docker Architecture

Docker traditionally uses a background daemon.

```text
docker command
      ↓
Docker Daemon
   (dockerd)
      ↓
Containers
```

Every Docker command communicates with the Docker daemon.

The daemon continuously runs in the background.

---

# The Docker Daemon Problem

Traditionally, the Docker daemon runs with root privileges.

This creates two concerns:

1. A continuously running background service is required.
2. The daemon is a highly privileged process.

This architecture increases the security impact of daemon-level vulnerabilities or misconfiguration.

---

# Podman

Podman uses a daemonless architecture.

```text
podman command
       ↓
Container Process
```

No central daemon is required.

Podman also supports rootless containers.

```text
DOCKER                     PODMAN

Daemon                     Daemonless
Traditionally Root         Rootless Support

```

For most basic workflows, the commands are very similar.


---

# The Docker workflow

## Developer

```bash
git clone <repository>

docker compose up
```

## Deployment

```bash
docker pull <image>

docker run <image>
```

The environment travels with the application.

---

# Key Takeaway

Docker helps us package applications into portable images.

Images create isolated running containers.

Volumes persist data.

Docker Compose defines complete multi-container applications.

```text
BUILD → SHIP → RUN
```
