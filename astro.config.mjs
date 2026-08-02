import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const base = process.env.BASE_PATH || '/';
const normalizedBase = base === '/' ? '/' : `/${base.replace(/^\/+|\/+$/g, '')}`;

const defaultSite = process.env.CF_PAGES === '1'
  ? 'https://pravartak.pages.dev'
  : 'https://example.com';

export default defineConfig({
  site: process.env.SITE_URL || defaultSite,
  base: normalizedBase,
  output: 'static',
  trailingSlash: 'always',
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
  integrations: [
    starlight({
      title: 'Pravartak',
      description: 'A practical AI, cloud, and DevOps learning path.',
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      lastUpdated: false,
      pagination: true,
      sidebar: [
        { label: 'Start here', items: [{ slug: 'getting-started' }] },
        {
          label: 'LLM foundations',
          collapsed: true,
          items: [{ autogenerate: { directory: 'llm-foundations' } }],
        },
        {
          label: 'LLM pretraining',
          collapsed: true,
          items: [{ autogenerate: { directory: 'llm-pretraining' } }],
        },
        {
          label: 'Retrieval & RAG',
          collapsed: true,
          items: [{ autogenerate: { directory: 'retrieval-rag' } }],
        },
        {
          label: 'Agents & workflows',
          collapsed: true,
          items: [{ autogenerate: { directory: 'agents-workflows' } }],
        },
        {
          label: 'Local LLMs & CLI',
          collapsed: true,
          items: [{ autogenerate: { directory: 'local-llms-cli' } }],
        },
        {
          label: 'Fine-tuning & evals',
          collapsed: true,
          items: [{ autogenerate: { directory: 'finetuning-eval' } }],
        },
        {
          label: 'Containers & DevOps',
          collapsed: true,
          items: [{ autogenerate: { directory: 'containers-devops' } }],
        },
        {
          label: 'AWS deployment',
          collapsed: true,
          items: [{ autogenerate: { directory: 'aws-cloud' } }],
        },
        {
          label: 'Specialized topics',
          collapsed: true,
          items: [{ autogenerate: { directory: 'specialized' } }],
        },
      ],
      head: [
        { tag: 'meta', attrs: { name: 'theme-color', content: '#07111f' } },
        { tag: 'meta', attrs: { property: 'og:type', content: 'website' } },
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
          },
        },
      ],
    }),
  ],
});
