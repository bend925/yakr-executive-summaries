# Yakr Brand & Style Reference

## Colours

| Token | Hex | Usage |
|---|---|---|
| `--yakr-red` | `#ff004f` | Primary actions, active tabs, progress bars, accents |
| `--yakr-green` | `#0ae57d` | Success states, confirmations |
| `--yakr-blue` | `#034dff` | (Reserved — not currently used in UI) |
| `--yakr-black` | `#000000` | Sidebar background, download buttons, headings |
| `--yakr-dark` | `#111111` | Dark surface fallback |
| `--yakr-gray` | `#f7f7f8` | Light surface backgrounds |
| `--yakr-border` | `#e5e5e5` | Card and table borders |

## Typography

- **Font:** Satoshi — loaded via `https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap`
- **Weights used:** 400 (body), 500 (medium), 700 (bold headings/buttons), 900 (display)
- **Email output font:** Calibri, Arial, sans-serif — 11pt, colour `#222`

## Logo & Assets

| File | Usage |
|---|---|
| `assets/yakr-logo-red-transparent.png` | Main logo — used in sidebar and login page (width: 120–160px) |
| `assets/yakr-icon-black.png` | Favicon / page icon |

Logos are embedded as base64 in the Streamlit app to avoid file-serving issues.

## UI Component Styles

### Sidebar
- Background: `#000000` (black)
- All text: `white`
- Expander/input surfaces: `#1a1a1a`
- Borders: `#333`
- Dividers: `#333`

### Buttons
- **Primary (Generate):** `background: #ff004f`, white text, `border-radius: 8px`, bold, hover lifts with red shadow
- **Secondary / sidebar buttons:** `background: #333`, white text, `border: 1px solid #555`
- **Download:** `background: #000000`, white text

### Cards / Metric tiles
- `background: white`, `border: 1px solid #e5e5e5`, `border-radius: 12px`, subtle box shadow

### Tabs
- Active tab: `border-bottom-color: #ff004f`, text `#ff004f`

### Progress bar
- Fill colour: `#ff004f`

### Status pills
- Active/success: `background: #f0fff5`, `color: #059040`
- Neutral/no-movement: `background: #f5f5f5`, `color: #888`

### Email preview container
- White card, `border-radius: 12px`, header underlined with `#ff004f` 2px border

## Writing Style (Client Emails)

- **Greeting:** "Morning [Name]," or "Afternoon [Name]," — never "Hi"
- **Tone:** Warm but professional — like a trusted advisor giving a friend a business update
- **Brevity:** 2–4 short sentences per candidate. No filler phrases.
- **Sign-off:** "Kind regards,\n\nJoe."
- **Plain English:** No status codes, no acronyms the client wouldn't know
- **Flag for review:** Use `[REVIEW - reason]` for anything requiring human judgement before sending

## Streamlit Config

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#ff004f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f7f7f8"
textColor = "#111111"
font = "sans serif"
```

## Secrets Required (Streamlit Cloud)

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
APP_PASSWORD = "yakr2026"
```
