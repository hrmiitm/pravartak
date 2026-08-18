---
title: Docker basics
description: Package, ship, and run applications in portable containers.
sidebar:
  order: 1
---

# Docker basics

**Docker** is a platform for building, sharing, and running **containers** — isolated environments that package an application together with its runtime, dependencies, and configuration. It solves the classic *"but it works on my machine"* problem for both development and deployment.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Slides · drawing tools · PDF</small></p>
  <a href="../../slides/docker/">Open slide deck →</a>
</div>

## 1. Images and containers

Docker is built around two core concepts:

| Concept | What it is | Analogy |
| --- | --- | --- |
| **Image** | A static, packaged artifact containing application code, runtime, dependencies, and configuration | A blueprint |
| **Container** | A running instance of an image | A running instance built from that blueprint |

An image never changes once built. A container is the live, executing process created from it. One image can start many containers, and each container gets its own isolated filesystem and process space.

```text
Docker Image
     ↓
 docker run
     ↓
Running Container
```

## 2. Images are built from layers

An image isn't one big file — it's a stack of **layers**, where each layer is the filesystem change produced by one instruction in a Dockerfile (`FROM`, `RUN`, `COPY`, and so on). Layers are cached, read-only, and stacked on top of each other:

```text
Application Code Layer      (COPY . .)
Dependencies Layer          (RUN pip install -r requirements.txt)
Language Runtime Layer      (python:3.12-slim)
Base Operating System Layer (Debian / Alpine Linux)
```

The **base layer** is almost always a minimal Linux distribution, because containers rely on the Linux kernel's isolation features (see below). Everything you add — a language runtime, your dependencies, your application code — is stacked as new layers on top of that base.

This layering is why Docker builds are fast after the first one: if only your application code changes, Docker reuses the cached base, runtime, and dependency layers, and only rebuilds the layer that changed.

:::note
Layers are also why two images that share the same base (e.g. two apps both built `FROM python:3.12-slim`) don't need to store that base twice on a machine — Docker stores and reuses shared layers on disk.
:::

## 3. Containers vs. virtual machines

Containers are often compared to virtual machines because both provide isolation, but they isolate at different levels:

| | Virtual Machine | Container |
| --- | --- | --- |
| Isolation unit | Full guest operating system | A process, isolated by the kernel |
| Runs on top of | A hypervisor | The host's own kernel |
| Boot time | Seconds to minutes | Milliseconds to seconds |
| Size | Gigabytes (full OS) | Megabytes to low gigabytes |
| Resource overhead | High — each VM duplicates an OS | Low — kernel is shared |
| Typical use | Running different operating systems on one host | Packaging and isolating one application |

```text
VIRTUAL MACHINE STACK          CONTAINER STACK

┌───────────────┐              ┌───────────────┐
│  Application   │              │  Application   │
├───────────────┤              ├───────────────┤
│  Guest OS      │              │  Container     │
├───────────────┤              │  Runtime Layer │
│  Hypervisor    │              ├───────────────┤
├───────────────┤              │  Docker Engine │
│  Host OS       │              ├───────────────┤
├───────────────┤              │  Host OS       │
│  Hardware      │              ├───────────────┤
└───────────────┘              │  Hardware      │
                                └───────────────┘
```

A VM virtualizes hardware and boots an entire guest operating system for every instance. A container shares the host machine's Linux kernel and is isolated from other processes using kernel features (namespaces and cgroups), so it only needs to ship the application layer, not a whole OS. This is why containers start almost instantly and are far lighter than VMs.

:::caution
Because containers share the host kernel, a Linux container needs a Linux kernel to run on. On macOS and Windows, Docker Desktop runs a small Linux VM behind the scenes to provide that kernel — the container itself is still lightweight, but the underlying machine still needs some form of Linux to host it.
:::

## 4. Basic Docker commands

Run these to work with images and start containers:

| Command | What it does |
| --- | --- |
| `docker pull <image>` | Download an image from a registry |
| `docker images` | List images stored locally |
| `docker run <image>` | Create and start a container from an image |
| `docker run -p HOST_PORT:CONTAINER_PORT <image>` | Start a container and map a container port to a host port |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers, including stopped ones |

Example — run a web server without installing anything on the host:

```bash
docker pull nginx
docker run -p 8080:80 nginx
```

Then open `localhost:8080` in a browser. The `HOST_PORT:CONTAINER_PORT` format tells Docker to forward traffic from your machine's port to the isolated port inside the container.

## 5. Managing containers

Once containers are running, use these commands to inspect and control them:

| Command | What it does |
| --- | --- |
| `docker stop <container>` | Stop a running container |
| `docker rm <container>` | Remove a stopped container |
| `docker logs <container>` | View a container's output |
| `docker exec -it <container> sh` | Open a shell inside a running container |

```bash
docker stop my-app
docker rm my-app
docker logs my-app
docker exec -it my-app sh
```

:::caution
`docker rm` only works on stopped containers by default, and it deletes the container's writable layer permanently. Any data written inside the container (and not stored in a volume — see below) is lost when the container is removed.
:::

## 6. Building your own image with a Dockerfile

A **Dockerfile** contains the instructions Docker uses to build an image, layer by layer:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV APP_ENV=production

CMD ["python", "app.py"]
```

| Instruction | Purpose |
| --- | --- |
| `FROM` | Sets the base image (usually a minimal Linux + runtime layer) |
| `WORKDIR` | Sets the working directory inside the image |
| `COPY` | Copies files from the host into the image |
| `RUN` | Executes a command while building the image (e.g. installing dependencies) |
| `ENV` | Sets an environment variable available inside the container |
| `CMD` | Sets the default command run when a container starts |

Build and run it:

```bash
docker build -t my-app .
docker run -p 8000:8000 my-app
```

To share the image with a teammate, push it to a registry such as Docker Hub:

```bash
docker push username/my-app

# on the teammate's machine
docker pull username/my-app
docker run username/my-app
```

## 7. Persisting data with volumes

Container filesystems are **ephemeral** — when a container is removed, any data written inside it disappears too. This is a problem for databases, uploaded files, and any stateful application.

A **volume** stores data outside the container's writable layer, on the host, so it survives even after the container is removed:

```bash
docker volume create app-data

docker run \
  -v app-data:/app/data \
  my-app
```

Anything written to `/app/data` inside the container is actually stored in the `app-data` volume. A new container can mount the same volume and pick up right where the old one left off.

## 8. Running multiple containers with Docker Compose

Real applications usually need more than one container — a web app, a database, a cache. **Docker Compose** describes an entire multi-container application in a single `compose.yaml` file:

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

```bash
docker compose up
```

This single command builds (if needed), creates, and starts every service defined in the file, wired together with the ports and volumes you specified.

## 9. Docker vs. Podman

Docker and Podman solve the same problem — building and running containers — but differ in architecture:

| | Docker | Podman |
| --- | --- | --- |
| Architecture | Background daemon (`dockerd`) | Daemonless |
| Privileges | Traditionally runs as root | Supports rootless containers |
| Command | `docker run`, `docker build` | `podman run`, `podman build` |

Docker traditionally relies on a continuously running, highly privileged daemon that every command talks to. Podman has no central daemon — each `podman` command runs the container directly — and it supports running containers without root privileges. For most everyday workflows the commands are close to interchangeable.

## 10. Troubleshoot a container

1. Check whether it's running: `docker ps` (or `docker ps -a` for stopped containers).
2. Read its output: `docker logs <container>`.
3. Get a shell inside it to inspect the environment: `docker exec -it <container> sh`.
4. If a port isn't reachable, confirm the `-p HOST_PORT:CONTAINER_PORT` mapping matches the port the application actually listens on inside the container.
5. If data disappeared after removing a container, check whether it was writing to a volume or to the container's own (ephemeral) filesystem.

## Practice

Pull the `nginx` image, run it mapping host port `8080` to container port `80`, and confirm it's reachable at `localhost:8080`. Then write a one-line Dockerfile-based app of your own, build it with `docker build -t my-app .`, and run it with a mounted volume so a file you write inside `/app/data` survives a `docker rm` and a fresh `docker run`.

[Read the Docker documentation](https://docs.docker.com/)

[Read about Podman](https://podman.io/)

[Open the Docker slides](../../slides/docker/)
