---
marp: true
title: LXD Sandboxing Basics
description: Run and manage a disposable Linux container
theme: default
size: 16:9
paginate: true
---

# Docker or LXD?

Both use containers. Choose the tool that matches the job.

| Docker | LXD |
| --- | --- |
| Package and ship one application or service. | Run a complete Linux lab or development sandbox. |
| Best for CI/CD, deployment, and Kubernetes workflows. | Best for system testing, resource controls, snapshots, and devices. |
| Usually focused on one process. | A reusable environment with a shell and full Linux user space. |

**Why:** use Docker to deliver applications; use LXD when you need a machine-like, disposable Linux environment.

<!-- notes
This deck uses one disposable container called lab. The first slide helps learners choose between Docker and LXD. LXD manages instances; lxc is the command-line client.
-->

---

## The simple mental model

~~~text
Host Linux
    ↓ runs
LXD service
    ↓ manages
Container: lab
~~~

- lxd is the service
- lxc is the client command
- A container has its own files and processes
- Containers share the host Linux kernel

> LXD access is highly privileged. Give it only to trusted users.

---

## Launch a running container

~~~bash
lxc launch ubuntu:24.04 lab
lxc list
lxc shell lab
~~~

- launch creates and starts the container
- list shows its state and IP address
- shell opens a login shell

~~~bash
lxc exec lab -- uname -a
~~~

lxc exec runs one command without opening a shell.

---

## Limit CPU, RAM, and root disk

~~~bash
lxc config set lab limits.cpu=2 limits.memory=2GiB
lxc config device override lab root size=10GiB
~~~

Check from the container:

~~~bash
lxc exec lab -- nproc
lxc exec lab -- free -h
lxc exec lab -- df -h /
~~~

override creates a per-container root-disk setting when root came from the default profile.

---

## Attach a GPU carefully

~~~bash
# inspect hardware on the host
lxc info --resources
nvidia-smi -L

# replace with your real PCI address
lxc config device add lab gpu0 gpu gputype=physical pci=0000:01:00.0
~~~

~~~bash
lxc exec lab -- nvidia-smi
~~~

- GPU access is device pass-through, not a simple quota
- Attach only hardware that the workload really needs
- Host drivers and container userspace must be compatible

---

## Transfer files with lxc file

~~~bash
# host → container
lxc file push hello.txt lab/root/hello.txt

# container → host
lxc file pull lab/root/hello.txt ./hello-from-lab.txt
~~~

~~~text
Host file  ── push ──>  lab:/root/hello.txt
Host file  <─ pull ───  lab:/root/hello.txt
~~~

Add -r when copying a directory recursively.

---

## Use snapshots and reusable settings

~~~bash
# save a rollback point
lxc snapshot lab before-change

# return to it later
lxc restore lab before-change
~~~

- **Profiles** reuse common limits, devices, and networking
- **Custom volumes** keep data outside a single instance
- **Proxy devices** forward a chosen host port to a chosen container port

> A snapshot is not an off-host backup.

---

## A safe beginner workflow

1. Launch lab.
2. Limit CPU, RAM, and disk.
3. Work with shell, exec, and file.
4. Take a snapshot before risky changes.
5. Delete the lab when finished.

~~~bash
lxc config show lab --expanded
lxc delete lab --force
~~~

**Practice:** set 2 CPUs, 2 GiB RAM, and 10 GiB disk; move a file; then restore a snapshot.

---

## Safely test a coding tool

For Claude Code or another assistant, create a separate disposable lab. Do **not** mount host folders, attach a GPU, or copy secrets into it.

~~~bash
lxc launch ubuntu:24.04 ai-lab
lxc config set ai-lab limits.cpu=2 limits.memory=4GiB limits.processes=512 limits.memory.swap=false
lxc config device override ai-lab root size=12GiB
~~~

~~~bash
lxc exec ai-lab -- apt update && apt install -y curl git
lxc exec ai-lab -- useradd -m -s /bin/bash coder
lxc exec ai-lab -- su - coder
# Claude Code: curl -fsSL https://claude.ai/install.sh | bash
~~~

- Use a throwaway repository. Review permission prompts and edits; never bypass approvals.
- LXD shares the host kernel. Do not use it for hostile code; delete the lab when finished.
