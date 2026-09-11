# Book a Trip — an SEO-driven travel site, built as a case study

A small British Columbia travel-planning site built to *apply* SEO methodology end to end,
not just to look like a site with keywords in it. Every content and structural decision on
this project traces back to real keyword research and real SERP analysis.

**This is a portfolio / learning project — not a licensed travel agency, and no real
bookings or payments are processed.**

---

## What this project demonstrates

| Area | What was actually done |
|---|---|
| **Keyword research** | Seed keywords → modifier expansion → the five-point checklist (search demand, traffic potential, business potential, search intent, ranking difficulty), using real Ahrefs (Canada) volume/KD data |
| **SERP analysis** | Live searches for every target keyword; competitor pages fetched and read in full, not summarised from snippets |
| **Content-gap analysis** | Ahrefs Content Gap methodology (2–3 competitor targets, "2 targets / 3 targets" intersections) — implemented as a working internal tool at `/content-gap` |
| **Link building** | Ahrefs five-attribute scorecard (relevance, authority, anchor text, follow status, placement) applied to five real BC travel/relocation pages, actually read and graded — implemented as a working internal tool at `/link-prospects` |
| **On-page SEO** | Title tags, descriptive URL slugs, meta descriptions, H1–H3 structure, internal linking, `aria-hidden` on decorative SVGs (the site has no raster images), OG tags, `WebSite` / `Article` / `FAQPage` schema |
| **Technical SEO** | `robots.txt`, dynamic `sitemap.xml`, canonical tags, a real `noindex` on the per-booking confirmation page, a proper 404 with the correct status code |
| **Honest measurement** | No invented traffic, rankings, or Search Console numbers anywhere. Where a metric needs a paid tool, it's labelled "Needs verification" rather than guessed |

## Pages built from validated research

- `/` — homepage + trip-planning flow, two accessibly-priced tiers ($15 self-guided / $49 full session)
- `/destinations/british-columbia/weekend-trips-from-vancouver/` — the first `TARGET NOW` keyword
- `/destinations/british-columbia/vancouver-to-nanaimo-ferry/` — primary keyword `vancouver to nanaimo ferry` (>1,000/mo, KD Easy, Canada): BC Ferries vs. Hullo comparison, the content gap no competitor filled

## Internal research tooling

Three internal, noindexed, `robots.txt`-blocked tools back the research process:

- **`/research`** — keyword-research worksheet mirroring the five-point checklist template
- **`/content-gap`** — Content Gap log mirroring the Ahrefs tool's exact columns and intersections filter
- **`/link-prospects`** — link-prospect log mirroring the link-building module's five-attribute scorecard; seeded with five real BC travel/relocation pages actually read and graded against it

All three persist to an embedded SQLite database and only ever hold data entered from a real tool run or a page someone actually opened and read.

---

## Running it locally

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Then open <http://localhost:5090>. The SQLite database is created automatically on first run.

Payment handling is wired for Stripe but falls back to a demo flow until real keys are added
to `backend/.env` (see `backend/.env.example`). No card details are collected in either mode.

## Stack

Flask · vanilla HTML/CSS/JS · embedded SQLite · no build step.
