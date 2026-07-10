import { describe, it, expect } from 'vitest';
import { parseScalar, parseDeck } from './slides';

describe('parseScalar', () => {
  it('should trim whitespace and remove surrounding quotes', () => {
    expect(parseScalar("  'hello'  ")).toBe('hello');
    expect(parseScalar('  "world"  ')).toBe('world');
    expect(parseScalar('no-quotes')).toBe('no-quotes');
  });
});

describe('parseDeck', () => {
  it('should parse metadata and markdown slides correctly', () => {
    const markdown = `---
title: Test Title
description: Test Description
---
# Slide 1
Some content

<!-- notes
First slide notes
-->
---
## Slide 2
Other content
`;
    const result = parseDeck(markdown);
    expect(result.meta.title).toBe('Test Title');
    expect(result.meta.description).toBe('Test Description');
    expect(result.slides).toHaveLength(2);
    expect(result.slides[0].label).toBe('Slide 1');
    expect(result.slides[0].notes).toBe('First slide notes');
    expect(result.slides[1].label).toBe('Slide 2');
    expect(result.slides[1].notes).toBe('');
  });
});
