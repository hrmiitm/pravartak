import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';

const base = process.env.BASE_PATH || '/';
const normalizedBase = base === '/' ? '/' : `/${base.replace(/^\/+|\/+$/g, '')}`;

const defaultSite = process.env.CF_PAGES === '1'
  ? 'https://pravartak.pages.dev'
  : 'https://example.com';

const docsDirectory = fileURLToPath(new URL('./src/content/docs/', import.meta.url));
const markdownFile = /\.(?:md|mdx)$/;

function frontmatterTitle(filePath) {
  const source = readFileSync(filePath, 'utf8');
  const frontmatter = source.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  const title = frontmatter?.[1].match(/^title:\s*["']?(.+?)["']?\s*$/m)?.[1];
  return title?.trim();
}

function fallbackLabel(name) {
  return name.replace(/[-_]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function titleForDirectory(name) {
  for (const fileName of ['overview.md', 'overview.mdx', 'index.md', 'index.mdx']) {
    const filePath = `${docsDirectory}/${name}/${fileName}`;
    if (existsSync(filePath)) return frontmatterTitle(filePath) || fallbackLabel(name);
  }
  return fallbackLabel(name);
}

const docsEntries = readdirSync(docsDirectory, { withFileTypes: true });
const generatedSidebar = [
  ...docsEntries
    .filter((entry) => entry.isFile() && markdownFile.test(entry.name) && !entry.name.startsWith('index.'))
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((entry) => {
      const filePath = `${docsDirectory}/${entry.name}`;
      return {
        slug: entry.name.replace(markdownFile, ''),
        label: frontmatterTitle(filePath) || fallbackLabel(entry.name.replace(markdownFile, '')),
      };
    }),
  ...docsEntries
    .filter((entry) => entry.isDirectory())
    .sort((a, b) => titleForDirectory(a.name).localeCompare(titleForDirectory(b.name)))
    .map((entry) => ({
      label: titleForDirectory(entry.name),
      collapsed: true,
      items: [{ autogenerate: { directory: entry.name, collapsed: true } }],
    })),
];

export default defineConfig({
  site: process.env.SITE_URL || defaultSite,
  base: normalizedBase,
  output: 'static',
  trailingSlash: 'always',
  // Some classroom and shared Linux machines exhaust their inotify watcher limit.
  // Polling keeps `npm run dev` usable there without requiring sudo/sysctl access.
  vite: {
    server: {
      watch: {
        usePolling: true,
        interval: 700,
      },
    },
  },
  integrations: [
    starlight({
      title: 'Pravartak',
      description: 'A practical AI, cloud, and DevOps learning path.',
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      lastUpdated: false,
      pagination: true,
      sidebar: generatedSidebar,
      head: [
        { tag: 'meta', attrs: { name: 'theme-color', content: '#07111f' } },
        { tag: 'meta', attrs: { property: 'og:type', content: 'website' } },
      ],
    }),
  ],
});
