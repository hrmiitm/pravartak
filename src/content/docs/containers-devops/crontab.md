---
title: Crontab basics
description: Schedule a small command safely on Linux.
sidebar:
  order: 2
---

# Crontab basics

**Cron** is a Linux service that runs commands on a schedule. A **crontab** is the schedule file for one user. It is useful for reports, cleanup jobs, backups, and small health checks.

## 1. Learn the crontab commands

Run these commands as the user who should own the job:

```bash
crontab -e       # edit this user's schedule
crontab -l       # list this user's scheduled jobs
crontab -r       # remove this user's schedule — use with care
sudo crontab -u appuser -l  # list another user's jobs (administrator only)
```

`crontab -e` opens an editor. Save and close it to install the new schedule. Always use `crontab -l` afterwards to confirm what was saved.

:::caution
`crontab -r` deletes every job for that user without asking. Prefer `crontab -e` and remove one line at a time.
:::

## 2. Understand one cron line

```text
# minute hour day-of-month month day-of-week command
0      9    *            *     1-5         /home/user/app/report.sh
```

This runs at **09:00**, Monday through Friday. The five time fields are read from left to right:

| Field | Allowed values | Example | Meaning |
| --- | --- | --- | --- |
| Minute | `0-59` | `30` | At 30 minutes past the hour |
| Hour | `0-23` | `18` | At 6 PM |
| Day of month | `1-31` | `1` | On the first day of a month |
| Month | `1-12` or `JAN-DEC` | `1,7` | January and July |
| Day of week | `0-7` or `SUN-SAT` | `MON-FRI` | Weekdays (`0` and `7` are Sunday) |

## 3. Use the scheduling symbols

```text
*          every value                 */15       every 15 values
,          a list                      1,15       first and fifteenth
-          a range                     MON-FRI    Monday to Friday
/          a step                      9-17/2     every two hours from 9 to 17
```

Practical schedules:

```text
*/15 * * * * /home/user/app/check.sh        # every 15 minutes
0 0 * * * /home/user/app/backup.sh          # every day at midnight
30 8 * * MON-FRI /home/user/app/report.sh   # 8:30 AM on weekdays
0 8 1 * * /home/user/app/monthly.sh         # 8 AM on the first of each month
0 2 1 JAN,JUL * /home/user/app/audit.sh     # 2 AM on 1 January and 1 July
```

Cron also provides useful shortcuts:

```text
@reboot   /home/user/app/startup-check.sh    # once after the cron service starts
@daily    /home/user/app/backup.sh           # once a day
@weekly   /home/user/app/weekly-report.sh    # once a week
@monthly  /home/user/app/monthly-report.sh   # once a month
```

## 4. Create a job that can be trusted

Make a small script first:

```bash
#!/usr/bin/env bash
set -euo pipefail

date --iso-8601=seconds
echo "Creating the daily report"
```

Save it as `/home/user/app/report.sh`, then make it executable and test it:

```bash
chmod +x /home/user/app/report.sh
/home/user/app/report.sh
```

Only then schedule it. Capture both normal output and errors:

```text
0 9 * * 1-5 /home/user/app/report.sh >> /home/user/app/logs/report.log 2>&1
```

- `>>` appends normal output to a log instead of replacing the file.
- `2>&1` sends error output to the same log.
- `set -euo pipefail` stops a Bash script when a command fails, an unset variable is used, or a pipeline fails.

## 5. Environment, paths, and safety

Cron has a much smaller environment than your terminal. Set what you need at the top of the crontab:

```text
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=""

0 9 * * 1-5 /home/user/app/report.sh >> /home/user/app/logs/report.log 2>&1
```

- `SHELL` chooses the shell used for command lines.
- `PATH` helps cron find commands, but full paths are still clearest.
- `MAILTO=""` disables cron email; use a log instead. Set an address only when local mail is configured.
- Never put passwords, tokens, or API keys directly in a crontab. Read protected secrets from a secret manager or a file with strict permissions.
- Make jobs **idempotent**: running the job twice should not send duplicate emails, charge twice, or create duplicate records.

## 6. Troubleshoot a job

1. Run the exact command manually as the same user.
2. Confirm the job exists with `crontab -l`.
3. Read the log file you configured.
4. Check that the cron service is running:

```bash
systemctl status cron     # Debian/Ubuntu
systemctl status crond    # Fedora/RHEL family
```

5. Check system logs if the job never starts:

```bash
journalctl -u cron --since today
journalctl -u crond --since today
```

For a job that must not overlap with itself, use a lock:

```text
*/5 * * * * flock -n /tmp/report.lock /home/user/app/report.sh >> /home/user/app/logs/report.log 2>&1
```

`flock -n` skips a new run while a previous run still holds the lock.

## Practice

Create a script that writes the current date to `~/cron-practice.log`. Run it every five minutes, confirm the log changes, then remove the line with `crontab -e`.

[Read the crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html)

[Read systemd timer documentation for more robust server scheduling](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)

[Open the crontab slides](../../slides/crontab/)
