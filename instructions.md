# Week 1: Getting Started with Playwright

## Objective
Get hands-on with the data layer of our knowledge graph by scraping a single Amazon product page, then generalize the approach with a reusable configuration.

## Tasks
- Use Playwright to scrape an Amazon product page and extract:
  - Product name, description, price, images
  - Any other key attributes (e.g., rating, number of reviews, variants)
- Generalize your scraper so it works for any Amazon product URL using a configuration file.
  - Provide a function like `foo(url)` that loads a default Amazon config and returns structured data.
  - Ideally support `foo(url, config_file)` to allow custom configs (optional).
- Leave comments in areas that make sense.

## Deliverables
- A working Playwright script that scrapes one product page.
- A configuration file for Amazon and a function that accepts a URL (and optionally a config file).

## Why this matters
- Build practical familiarity with Playwright and our data ingestion flow.
- Produce an up-to-date Amazon config and set the pattern for other e-commerce sites.
- Set the stage for exploring automation (e.g., LLM-driven selectors vs. manual) and reducing redundancy.

## Important note
When installing Python packages, use `uv` instead of `pip` so everything stays managed by our project tool.
- Install packages with: `uv add <package-name>`
- Example: `uv add playwright`

## Helpful resources
- Playwright scraping guide: https://oxylabs.io/blog/playwright-web-scraping