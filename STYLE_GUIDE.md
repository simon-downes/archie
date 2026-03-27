# Output Style Guide

Defines the visual language for all Archie CLI output. Theme colours are reserved for the startup banner only — all operational output uses a fixed palette.

## Colour Palette

| Constant | Colour | Role | Use for |
|----------|--------|------|---------|
| `C_HEADING` | bright_magenta | Headings | Section titles in rules |
| `C_KEY` | bright_blue | Keywords | Resource names, service names, identifiers |
| `C_CMD` | bright_cyan | Commands | Runnable commands, CLI invocations |
| `C_VAL` | #5f87d7 | Values | Paths, filenames, data values |
| `C_PLAIN` | white | Body text | Descriptions, explanations, default text |
| `C_MUTED` | bright_black | Secondary | Types, timestamps, durations, sublabels |
| `C_CHROME` | dim | Decorative | Rules, bullets, separators, borders |
| `C_OK` | #50c878 | Success | ✓ icon only |
| `C_WARN` | #f0c050 | Warning | ! icon only |
| `C_ERR` | bright_red | Error | ✗ icon only |

### Rules

- Status colours (OK/WARN/ERR) are for icons only, never for text or chrome
- Theme colours are for the startup banner only, never for operational output
- Keywords (bright_blue) and values (#5f87d7) are related hues at different weights — keywords pop, values support
- Cyan is reserved for commands — things the user can copy and run
- When in doubt, use `C_PLAIN`

## Width

All output is capped at 80 characters. Set `Console(width=80)`.

## Primitives

### `section(title)`

Section header using a Rich rule with left-aligned title.

```
Credentials ────────────────────────────────────────────────────────────────────
```

- Title in `C_HEADING`
- Rule in `C_CHROME`
- Blank line above and below

### `status_table(*rows)`

Aligned table for status checks. Each row is `(ok, label, detail)` or `(ok, label, sublabel, detail)`.

```
  ✓      github          static      expires in 59m
  ✗      aws             static      not configured
```

- Icon column: `C_OK`/`C_ERR`/`C_WARN`
- Label column: `C_KEY`
- Sublabel column: `C_MUTED`
- Detail column: `C_MUTED` (override with markup for status-coloured expiry)

### `kv_table(*rows)`

Key-value pairs for config display.

```
  project_dir       ~/dev
  theme             blue
```

- Key column: `C_MUTED`
- Value column: `C_VAL`

### `msg_success(text)` / `msg_error(text)` / `msg_warn(text)` / `msg_info(text)`

Inline messages with status icon. Text accepts Rich markup for highlighting keywords, values, and paths.

```
  ✓  Installed to ~/.archie/
  ✗  Docker is not installed
  !  credentials.yaml has permissions 0644 — expected 0600
  →  Refreshed expired tokens for notion
```

- Icon: status colour (success/error/warn) or `C_KEY` for info arrow
- Text: `C_PLAIN` by default, embed `[C_KEY]`, `[C_VAL]`, `[C_CMD]` markup for highlights

### `bullet_list(items)`

Indented bullet list. Items accept Rich markup.

```
    •  ~/Library/Application Support/kiro-cli
    •  ~/.toad
```

- Bullet: `C_CHROME`
- Text: caller controls via markup

### `empty_state(text)`

Placeholder for empty results.

```
  No active sessions
```

- Text: `C_MUTED`

### `cmd(text)`

Standalone command display — something the user should copy and run.

```
    archie install
```

- Text: `C_CMD`

### `human_time(iso_timestamp)`

Converts ISO timestamps to relative human-friendly strings.

```
in 59m
2h ago
3d ago
```

## Timestamps

Always use `human_time()` for display. Never show raw ISO timestamps in user-facing output.

## Theme

Theme colours (`THEMES` dict) are used exclusively for the startup banner gradient. The banner is displayed once at container launch via `display_header()`. No other output uses theme colours.

Available themes: blue, purple, green, orange, cyan, red. Configured via `theme` in `~/.archie/config.yaml`.
