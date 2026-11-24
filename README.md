# Hypothetical COFs for CO2 Capture

Interactive exploration of 66,852 hypothetical two- and three-dimensional
covalent organic frameworks (COFs) screened for carbon capture: a scatter plot
of their computed properties, and a page with the structure and the properties
of each COF. Each COF page links its structure's AiiDA node in
[Materials Cloud Explore](https://www.materialscloud.org/explore/hcofs-co2)
("Explore the provenance"), where the old app's figure sent a click.
Data: [doi:10.24435/materialscloud:2020.0029/v1](https://doi.org/10.24435/materialscloud:2020.0029/v1)
(Materials Cloud Archive record `6yq0e-2be96`).

A static single-page app, the port of the Bokeh "discover-hcofs-co2" section of
Materials Cloud (the old app is commit [`f95d38b`](https://github.com/materialscloud-org/discover-hcofs-co2/tree/f95d38b) of this
repository; data decisions are documented in `scripts/prepareForFrontend.py`).

## Development

This app was migrated to a single page app, with the intention of providing users a serverless way to explore this data.

The legacy software, with tools to containerize it (which may be out of date), is commit [`f95d38b`](https://github.com/materialscloud-org/discover-hcofs-co2/tree/f95d38b) of this repository.

If you would like to launch the Single Page App locally:

```bash
pnpm install
python3 scripts/prepareForFrontend.py # about 3 minutes, ~9 GB memory
pnpm dev        # http://localhost:5173 (needs public/data/)
pnpm test       # node --test tests/*.test.mjs
pnpm lint
pnpm build      # static site in dist/ (copies public/data/: 1.3 GB)
```

## Deployment

The app is currently deployed by hand to Cloudflare Pages with wrangler with no CI/CD, so changes have to be pushed to materialscloud cloudflare. This is because of the sharding strategy used and that the data is too large for git and comes from the Materials Cloud Archive.

```bash
python3 scripts/prepareForFrontend.py  # if data is missing
pnpm build
npx wrangler pages deploy dist --project-name discover-hcofs-co2
```
