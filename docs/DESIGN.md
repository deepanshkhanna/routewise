# RouteWise Design System

Visual foundation: attached Shadcn UI Kit dark dashboard screenshot, adapted for network intelligence.

## Color tokens

| Token | Value | Role |
|-------|-------|------|
| `--rw-bg` | `#0a0a0a` | App background |
| `--rw-bg-sidebar` | `#0c0c0c` | Sidebar |
| `--rw-bg-elevated` | `#111111` | Header / elevated |
| `--rw-bg-card` | `#141414` | Cards / panels |
| `--rw-bg-muted` | `#1a1a1a` | Nested surfaces |
| `--rw-border` | `#27272a` | Hairline borders |
| `--rw-border-strong` | `#3f3f46` | Focus / hover border |
| `--rw-text` | `#fafafa` | Primary text |
| `--rw-text-muted` | `#a1a1aa` | Secondary |
| `--rw-text-faint` | `#71717a` | Tertiary |
| `--rw-primary` | `#fafafa` | Primary actions (inverted) |
| `--rw-primary-fg` | `#0a0a0a` | On primary |
| `--rw-success` | `#22c55e` | Healthy / up |
| `--rw-warning` | `#f59e0b` | Degraded |
| `--rw-danger` | `#f43f5e` | Failed / critical |
| `--rw-info` | `#60a5fa` | Informational |

Chart strokes: white/zinc grayscale with soft translucent fills — no rainbow series.

## Typography

- Family: Inter (UI), JetBrains Mono (metrics / IPs / CLI)
- Scale: 12 / 13 / 14 / 16 / 20 / 24 / 32
- Weights: 400, 500, 600
- Sentence case labels; no decorative all-caps eyebrows

## Spacing & radius

- Space: 4, 8, 12, 16, 20, 24, 32
- Radius: `--rw-radius-sm` 8px · `--rw-radius` 12px · `--rw-radius-lg` 16px
- Sidebar width: 260px

## Shadows & depth

Soft black elevation only: `0 0 0 1px var(--rw-border), 0 8px 24px rgba(0,0,0,.35)`

## Motion principles (Emil Kowalski)

- Animate occasional interactions (modals, page enter, path highlight)
- No animation on high-frequency keyboard actions
- Prefer `transform` + `opacity`, `ease-out`, 150–250ms
- Respect `prefers-reduced-motion`
- Packet motion is the signature delight — keep other motion quiet

## Components

Buttons, inputs, cards, badges, tables, tabs, toasts, metric tiles, charts, topology nodes — shared under `src/components/ui` and `src/components/layout`.
