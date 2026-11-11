# UI Skills & Design Research

## Already available
| Skill / capability | Location | Use |
|---|---|---|
| Vercel `shadcn` | Cursor vercel plugin cache | Visual language aligned with reference (zinc dark, cards, sidebar) |
| Vercel `react-best-practices` | Cursor vercel plugin cache | Component structure, a11y, perf |
| Chrome DevTools MCP | Session tools | Live browser inspection / screenshots |
| Canvas skill | `.cursor` / `.agents` | Not used for app UI (product app, not analytical canvas) |

## Loaded and used
- Screenshot reference → RouteWise token extraction (near-black surfaces, thin borders, muted charts)
- Vercel shadcn theming guidance → CSS variable design system (without migrating to Next.js)
- React best practices → modular pages, shared API layer, avoid unnecessary rerenders

## Newly installed (skills.sh)
- `anthropics/skills@frontend-design`
- `emilkowalski/skills@emil-design-eng`
- `vercel-labs/agent-skills@web-design-guidelines`

## Recommended but not installed
| Skill | Why skipped |
|---|---|
| Full shadcn CLI + Tailwind + Next template | Would force stack migration; Vite React already ships |
| Playwright CLI | Chrome DevTools MCP covers visual verification this sprint |
| pbakaus/impeccable | Not required after frontend-design + emil-design-eng |

## Design translation from screenshot
- Background ≈ `#0a0a0a`
- Cards ≈ `#111111`–`#141414` with `#27272a` borders
- Primary CTA: white on black
- Accents: emerald success, rose danger, amber warning (sparse)
- Charts: monochrome white/gray strokes with soft fills
- Radius: 12–16px
- Density: tight enterprise layout, not sparse marketing
