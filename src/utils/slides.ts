import { Marp } from '@marp-team/marp-core';

export type DeckMeta = { title: string; description?: string };
export type Slide = { html: string; notes: string; label: string };

export function parseScalar(value = '') {
  return value.trim().replace(/^['"]|['"]$/g, '');
}

export function parseDeck(source: string): { meta: DeckMeta; slides: Slide[]; css: string } {
  const frontmatter = source.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  const meta: DeckMeta = { title: 'Pravartak slides' };

  if (frontmatter) {
    for (const line of frontmatter[1].split(/\r?\n/)) {
      const separator = line.indexOf(':');
      if (separator < 0) continue;
      const key = line.slice(0, separator).trim() as keyof DeckMeta;
      if (['title', 'description'].includes(key)) {
        meta[key] = parseScalar(line.slice(separator + 1));
      }
    }
  }

  const marp = new Marp({ html: true, inlineSVG: false, printable: true });
  const rendered = marp.render(source, { htmlAsArray: true });
  const slides = rendered.html.map((html, index) => {
    const heading = html.match(/<h[1-3][^>]*>([\s\S]*?)<\/h[1-3]>/i)?.[1] || `Slide ${index + 1}`;
    const label = heading.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').trim();
    const notes = (rendered.comments[index] || [])
      .map((comment) => comment.replace(/^\s*notes\s*/i, '').trim())
      .filter(Boolean)
      .join('\n\n');
    return { html, notes, label };
  });

  return { meta, slides, css: rendered.css };
}
