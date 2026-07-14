---
title: Crontab basics
description: Schedule a small command safely on Linux.
sidebar:
  order: 2
---

# Crontab basics

**Cron** runs commands at chosen times. A **crontab** is the schedule file for one user.

## Your first scheduled command

1. Create a small script and run it yourself first.
2. Open your schedule with `crontab -e`.
3. Add a line like this:

```text
# minute hour day-of-month month day-of-week command
0 9 * * 1-5 /home/user/app/report.sh >> /home/user/app/report.log 2>&1
```

This runs `report.sh` at 9:00 AM, Monday to Friday. `>>` adds output to a log file and `2>&1` saves errors there too.

## Useful examples

```text
*/15 * * * * /home/user/app/check.sh       # every 15 minutes
0 0 * * * /home/user/app/backup.sh         # every day at midnight
0 8 1 * * /home/user/app/monthly.sh        # 8 AM on the first day of each month
```

## Beginner checklist

- Use full paths such as `/home/user/app/check.sh`.
- Make the script executable: `chmod +x /home/user/app/check.sh`.
- Look at the log file after the first run.
- Make retries safe: a job should not create duplicate records when it runs twice.
- Never place passwords or API keys in a crontab.

[Read the crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html)

[Open the crontab slides](../../slides/crontab/)
