# Prediction@Illinois

Website for Prediction@Illinois at the University of Illinois Urbana-Champaign: https://predictuiuc.com.

## Development

The site uses plain HTML, CSS, and JavaScript. No dependency installation or build step is needed.

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. Preview from the repository root so absolute asset and page URLs resolve correctly.

## Editing

- Homepage: `index.html`
- Research projects: `research/index.html`
- Team profiles: `team/index.html` and `assets/team/`
- Application link and recruitment text: `join/index.html`
- Shared styling: `styles.css`
- Hero image rotation and category controls: `app.js`
- Production imagery: `assets/photos/`; image provenance is in `assets/photos/image-sources.json`

Headers and footers are plain HTML repeated across the four pages; update all four when changing navigation or branding.

## Hosting

GitHub Pages publishes the repository root from `main`. `.nojekyll` disables Jekyll processing; `CNAME` retains the `predictuiuc.com` custom domain. Keep the Google Search Console verification file, `robots.txt`, and `sitemap.xml` when updating the site.

The old `/apply/` URL redirects to `/join/`. Former market pages redirect to the homepage or corresponding category; `/competitions/` and `/industry/` redirect to `/research/`. These are static HTML redirects with fallback links.

The redesign replaces the former live market board and ticker with a photographic category selector. Content is maintained directly in HTML rather than Jekyll YAML data files.
