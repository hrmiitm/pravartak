---
title: Getting started
description: How to learn with Pravartak and use its slide annotation tools.
sidebar:
  order: 1
---

Pravartak is a static learning site: no sign-in, tracking account, or server is required. Read lessons in order, try the small exercises, and use the slide decks for visual review.

## A useful rhythm

<ol class="learning-path">
  <li><strong>Preview.</strong> Scan the learning outcomes and the service or tool comparison.</li>
  <li><strong>Learn.</strong> Read the explanation and reproduce the smallest example.</li>
  <li><strong>Build.</strong> Complete the guided lab without copying blindly.</li>
  <li><strong>Summarize.</strong> Open the slides and restate the idea in your own words.</li>
  <li><strong>Verify.</strong> Use the checklist, then remove any paid cloud resources.</li>
</ol>

## Using slide decks

Every deck is a normal markdown file under `src/content/slides/`. In the viewer:

- Use the arrow keys, <kbd>Page Up</kbd>/<kbd>Page Down</kbd>, or the on-screen controls to navigate.
- Press <kbd>A</kbd> to open drawing tools and <kbd>N</kbd> to show notes.
- Pen, highlighter, and eraser strokes are saved automatically in this browser.
- **Export** downloads a JSON backup; **Import** restores it on another browser.
- Clearing site data also clears autosaved annotations, so export anything important.

## What you need

- A modern browser for reading and annotating.
- Node.js 20 or newer only if you edit or build the site.
- An AWS account for the deployment labs. Set a budget before creating resources.

:::caution
Cloud labs can create billable resources. Use least-privilege credentials, never commit secrets, and follow each cleanup checklist.
:::
