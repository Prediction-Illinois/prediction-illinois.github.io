# Prediction@Illinois

Website for Prediction@Illinois — the student research organization for prediction markets at
the University of Illinois Urbana-Champaign. https://prediction-illinois.github.io

**Fall 2026 applications are open.** Rolling, all majors, no finance background required.

## Editing the site

Built with GitHub Pages' native Jekyll — no local tooling. Push to `main` and the site rebuilds in about a minute.

| Want to… | Edit |
|---|---|
| Add or change a team member | `_data/team.yml` (one entry per person; the Team page and nav appear automatically once the list is non-empty) |
| Change a market's blurb, resolution source, or research questions | `_data/markets.yml` |
| Add a market | `_data/markets.yml` + a 6-line file in `markets/` (copy `markets/sports.html`) |
| Change the header / footer | `_includes/header.html`, `_includes/footer.html` |
| Styles / scripts | `assets/css/site.css`, `assets/js/site.js` |
| Receive applications by email | set `FORM_ENDPOINT` in `assets/js/site.js` to a Formspree URL |

Live market data comes from Polymarket's public Gamma API at page load.

---

Prediction@Illinois is not a Registered Student Organization and is not affiliated with,
endorsed by, or authorized to speak on behalf of the University of Illinois.
