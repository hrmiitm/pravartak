---
marp: true
title: Crontab Basics
description: Schedule one small Linux command
theme: default
size: 16:9
paginate: true
---

# Crontab basics

From first schedule to reliable background jobs.

---

## What cron does

```text
Your script → cron schedule → command runs → log file → you verify
```

- Good for reports, cleanup, backups, and checks
- Run scripts manually before scheduling them
- Use logs so failures are visible

---

## Manage your schedule

```bash
crontab -e       # edit jobs
crontab -l       # list jobs
crontab -r       # remove every job — careful
```

Use `crontab -l` after every edit.

---

## Read the five time fields

```text
minute  hour  day-of-month  month  day-of-week  command
0       9     *             *      1-5          /app/report.sh
```

Runs at 9 AM, Monday to Friday.

---

## Build schedules with symbols

```text
*       every value       */15    every 15 values
,       list              1,15    first and fifteenth
-       range             MON-FRI weekdays
/       step              9-17/2  every two hours from 9 to 17
```

```text
*/15 * * * * /app/check.sh       # every 15 minutes
@daily /app/backup.sh             # once a day
```

---

## Make a job reliable

1. Run the script yourself.
2. Add it with `crontab -e`.
3. Use full paths.
4. Save output to a log.

```text
0 9 * * 1-5 /app/report.sh >> /app/report.log 2>&1
```

`>>` appends output. `2>&1` adds errors to the same log.

---

## Debug and protect

```bash
systemctl status cron
journalctl -u cron --since today
```

- Cron has a minimal environment: set `PATH` or use absolute paths
- Keep secrets out of crontab lines
- Use `flock` when two runs must not overlap
- A retry-safe job should not create duplicate work
