---
marp: true
title: Crontab Basics
description: Schedule one small Linux command
theme: default
size: 16:9
paginate: true
---

# Crontab basics

Run a command at a chosen time.

---

## The cron format

```text
minute hour day month weekday command
0      9    *   *     1-5     /app/report.sh
```

Runs at 9 AM, Monday to Friday.

---

## Start safely

1. Run the script yourself.
2. Add it with `crontab -e`.
3. Use full paths.
4. Save output to a log.

```text
0 9 * * 1-5 /app/report.sh >> /app/report.log 2>&1
```
