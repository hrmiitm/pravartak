---
title: LXD sandboxing basics
description: Run a disposable Linux container and manage its resources.
sidebar:
  order: 6
---

# LXD sandboxing basics

**LXD** manages system containers and virtual machines. This short lab uses one container named **lab**. A container has its own processes, files, users, and network view, but it shares the host Linux kernel.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>9 slides · drawing tools · PDF</small></p>
  <a href="../../slides/lxd-sandboxing/">Open slide deck →</a>
</div>

## 1. Choose Docker or LXD

Both tools use Linux containers, but they are designed for different jobs:

| Choose Docker when | Choose LXD when |
| --- | --- |
| You need to package and run one application or service from an image. | You need a complete Linux environment for a lab, development workspace, multiple services, or system-level testing. |
| You are building a CI/CD, Kubernetes, or application-deployment workflow. | You need machine-like controls such as CPU/RAM/disk limits, snapshots, profiles, storage volumes, or hardware devices. |
| The container should be short-lived and focused on one process. | You want a reusable, disposable sandbox with a shell and an ordinary Linux user space. |

Docker is usually the better application-delivery tool. LXD is usually the better local systems lab or disposable development environment. Both Linux-container types share the host kernel; use a virtual machine or a dedicated sandbox service for code that is actively hostile or untrusted.

## 2. Know the two commands

- **lxd** is the background service that manages instances.
- **lxc** is the command-line client you use.

:::caution
Access to the local LXD service is highly privileged. A user who can manage LXD may be able to attach host paths or hardware to an instance. Add only trusted users to the lxd group.
:::

## 3. Prepare a small lab

The following is an Ubuntu example:

~~~bash
sudo snap install lxd
sudo usermod -aG lxd "$USER"
newgrp lxd
lxd init --minimal
~~~

Launch and enter a container:

~~~bash
lxc launch ubuntu:24.04 lab
lxc list
lxc shell lab
~~~

lxc launch creates and starts the container. Leave the shell with exit.

Run a single command from the host:

~~~bash
lxc exec lab -- uname -a
lxc exec lab -- bash -lc 'apt update && apt install -y htop'
~~~

Use bash -lc only when the command needs shell features such as &&, pipes, or variables.

## 4. Limit CPU, RAM, and storage

Set CPU and memory limits from the host:

~~~bash
lxc config set lab limits.cpu=2 limits.memory=2GiB
lxc config get lab limits.cpu
lxc config get lab limits.memory
~~~

Check from inside the container:

~~~bash
lxc exec lab -- nproc
lxc exec lab -- free -h
~~~

Set a 10 GiB root-disk limit:

~~~bash
lxc config device override lab root size=10GiB
lxc exec lab -- df -h /
~~~

The root disk is often inherited from the default profile, so override creates a per-container copy before changing it. Disk-size enforcement depends on the storage driver and available pool capacity.

## 5. Attach a GPU only when needed

First inspect the host:

~~~bash
lxc info --resources
nvidia-smi -L  # NVIDIA systems only
~~~

Attach one physical GPU by its PCI address:

~~~bash
lxc config device add lab gpu0 gpu gputype=physical pci=0000:01:00.0
lxc exec lab -- nvidia-smi
~~~

Replace the example PCI address with one from your host. GPU access is pass-through, not a harmless CPU-like quota; attach a GPU only to workloads you trust. The host driver and suitable userspace libraries must be available.

Remove the device when the lab is finished:

~~~bash
lxc config device remove lab gpu0
~~~

## 6. Transfer files

Push a host file into the container:

~~~bash
echo 'hello from host' > hello.txt
lxc file push hello.txt lab/root/hello.txt
lxc exec lab -- cat /root/hello.txt
~~~

Pull it back to the host:

~~~bash
lxc file pull lab/root/hello.txt ./hello-from-lab.txt
~~~

Add -r to either command when copying a directory recursively.

## 7. Use a few helpful LXD features

| Feature | Use it for | Example |
| --- | --- | --- |
| Snapshot | Quick rollback before a risky change | lxc snapshot lab before-change |
| Restore | Return to a snapshot | lxc restore lab before-change |
| Profile | Reuse a standard set of limits and devices | lxc profile create dev-small |
| Custom volume | Keep data outside one instance | lxc storage volume create default project-data |
| Proxy device | Forward one host port to the container | lxc config device add lab web proxy listen=tcp:0.0.0.0:8080 connect=tcp:127.0.0.1:80 |

:::note
A snapshot is a convenient rollback point, not an off-host backup plan. Back up important data and custom volumes separately.
:::

## Practice

1. Launch lab.
2. Set 2 CPUs, 2 GiB RAM, and a 10 GiB root disk.
3. Push in hello.txt, edit it, and pull it back out.
4. Take a before-change snapshot, create a test file, then restore the snapshot.
5. Review the result:

~~~bash
lxc config show lab --expanded
~~~

When finished, delete the disposable lab:

~~~bash
lxc delete lab --force
~~~

## Safely test Claude Code or another coding tool

Use a separate, disposable container for coding assistants. Do not mount a host project folder, attach a GPU, or copy secrets into this lab.

~~~bash
lxc launch ubuntu:24.04 ai-lab
lxc config set ai-lab limits.cpu=2 limits.memory=4GiB limits.processes=512 limits.memory.swap=false
lxc config device override ai-lab root size=12GiB
lxc exec ai-lab -- apt update
lxc exec ai-lab -- apt install -y ca-certificates curl git
lxc exec ai-lab -- useradd --create-home --shell /bin/bash coder
lxc exec ai-lab -- su - coder
~~~

Inside the container as the **coder** user, use the tool vendor's current installation instructions. For Claude Code, Anthropic currently documents:

~~~bash
curl -fsSL https://claude.ai/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"
claude --version
mkdir -p ~/demo && cd ~/demo && git init
claude
~~~

- Start with an empty or throwaway repository and review every command or edit.
- Do not use permission-bypass options such as Claude Code's --dangerously-skip-permissions.
- A container limits resources and keeps tool credentials and files away from your normal home directory, but it is **not** a strong boundary for malicious code because it shares the host kernel.
- When done, delete the whole environment, including its login credentials:

~~~bash
lxc delete ai-lab --force
~~~

[Read the official LXD first-steps guide](https://documentation.ubuntu.com/lxd/latest/tutorial/first_steps/)

[Read the LXD GPU-device reference](https://documentation.ubuntu.com/lxd/latest/reference/devices_gpu/)

[Read the official Claude Code installation guide](https://code.claude.com/docs/en/installation)

[Open the LXD sandboxing slides](../../slides/lxd-sandboxing/)
