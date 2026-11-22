# Numeraire, Risk-Neutral Measures & Girsanov — *Example First*

A static GitHub Pages explainer that teaches the scariest-sounding trio in
quant finance **through tiny hand-checkable numbers first, plain words second,
formulas last**. No measure theory assumed. Written for a BMS student aiming at
a quant career (and honestly, for anyone who fell asleep through change-of-numeraire lectures).

**Live site:** https://prakharquant.github.io/numeraire-girsanov/

## What's inside

| Ch. | Topic | Anchor example |
|-----|-------|----------------|
| 0 | Numeraire = unit of measurement | Laptop ₹60,000 vs $720 |
| 1 | Risk-neutral probability | 100 → 150/50 ⇒ q = 0.5; 130/80 ⇒ q = 0.4 |
| 2 | Binomial → Black-Scholes | CRR tree convergence table to 7.965 |
| 3 | Call = receive share − pay strike | strike leg = 100 × P(ITM) = N(d₂) seed |
| 4 | Change of numeraire (discrete) | reweight 0.5→0.75/0.25; three-state 12.5/50/37.5 |
| 5 | Price invariance | same call = 12 in rupees and in shares |
| 6 | N(d₂) as area, N(d₁) under the share ruler | d₂ = −0.1, d₁ = 0.1, C ≈ 7.96 |
| 7 | Girsanov | discrete reweighting → drift r → r + σ² |
| 8 | Forward measure | zero-coupon bond reweighting; forward rate = average |
| 9 | Cheat sheet | numeraires table + 4 big ideas |

Two vanilla-JS widgets: a **scenario reweighting slider** (Ch.4/5) and a
**bell-curve visualiser** with S/K/r/σ/T sliders showing the N(d₂) shaded area,
the σ√T-shifted curve for N(d₁), and the live Black-Scholes price (Ch.6).
Every chapter ends with a 3-question self-check behind "Show answer" toggles
and a "Common confusion" box. Light/dark mode, mobile-first, KaTeX via CDN.

## Repo layout

```
docs/               # served by GitHub Pages (branch main, folder /docs)
  index.html        # the whole site, one page, nine chapters
  css/style.css     # theme variables, cards, widgets
  js/app.js         # widgets (vanilla JS, no build step)
  js/data.json      # GENERATED — every number on the site lives here
scripts/verify.py   # numpy/scipy: recomputes everything, cross-checks HTML
```

## Run locally

```bash
cd docs
python3 -m http.server 8080          # open http://localhost:8080
```

Regenerate + verify all numbers (requires numpy & scipy):

```bash
python3 scripts/verify.py            # exits non-zero on ANY mismatch
```

`verify.py` writes `docs/js/data.json` (widget defaults + tables) and greps
`index.html` for every hardcoded figure it should match — if you edit a number
in the prose without re-running the script, CI-style checks will fail loudly.

## Learning path

```
 Ch.0 units ─▶ Ch.1 fake chances ─▶ Ch.2 trees→BS ─▶ Ch.3 option legs
                                                        │
 Ch.8 forward measure ◄─ Ch.7 Girsanov ◄─ Ch.6 bell slide ◄─ Ch.4/5 ruler swap
```

Order matters: each chapter only uses vocabulary the previous ones defined.

## How to contribute

1. Fork, edit `docs/index.html` (prose) or `scripts/verify.py` (numbers).
2. If you add a numeric example: compute it in `verify.py`, assert it there,
   then paste the script's output into the HTML. Never hand-type a figure the
   script doesn't produce.
3. Run `python3 scripts/verify.py` — must exit 0.
4. Open a PR. Keep paragraphs short; keep examples hand-checkable.

## Deploy (GitHub Pages)

Repo Settings → Pages → Source: **Deploy from a branch** → Branch: **main**,
folder: **/docs** → Save. The site publishes at
`https://<user>.github.io/numeraire-girsanov/`. No Actions workflow needed
(plain static files).

## Credits

Created by **[Prakhar Gupta](https://github.com/PrakharQuant)** · Quant Finance
· [bestofprakhar@gmail.com](mailto:bestofprakhar@gmail.com) ·
[LinkedIn](https://www.linkedin.com/in/prakhar-gupta-5b7250372/) ·
[X](https://x.com/PrakharQuant)

## License

MIT — see `LICENSE`.
