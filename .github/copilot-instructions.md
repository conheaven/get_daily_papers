# Copilot Instructions for Academic Paper Crawler

## Project Overview

This is a **web-based academic paper crawler** for top security conferences (NDSS, USENIX Security, CCS, S&P). It features:

- Dual data sources: DBLP (stable) + conference websites (detailed)
- Flask web UI for browsing papers with search/filter/pagination
- SQLite database with auto-deduplication
- Manual crawling (no scheduled tasks)

**Key Architecture**: `Flask UI (app.py) → Crawler Manager (main.py) → Database (database.py) → Crawlers (crawlers/) → Data Sources`

## Critical Setup

### First-Time Setup (REQUIRED)

```bash
pip install -r requirements.txt  # MUST run this before any crawling
python app.py                     # Start web interface (recommended)
```

**Common Issue**: If you see `lxml` parser errors, dependencies aren't installed. Run `pip install -r requirements.txt` first.

### Key Entry Points

- **Web Interface**: `python app.py` → `http://127.0.0.1:5000` (PREFERRED way to use the tool)
- **CLI**: `python main.py` for batch crawling
- **Database**: `papers.db` (auto-created, SQLite)

## Architecture Patterns

### 1. Crawler Registration System

Crawlers are registered in `main.py:CrawlerManager.__init__`:

```python
self.crawlers = {
    'NDSS': [DBLPCrawler('NDSS', config), NDSSCrawler('NDSS', config)],
    'NewConf': [DBLPCrawler('NewConf', config)]  # Add here
}
```

- Multiple crawlers per conference = multiple data sources
- Results auto-merged and deduplicated by (title, conference, year)

### 2. Two-Tier Crawler Design

- **`DBLPCrawler`** (in `crawlers/base.py`): Generic DBLP scraper, works for ANY conference in DBLP
- **Conference-specific crawlers** (in `crawlers/conference_crawlers.py`): Optional, for extracting abstracts/extra data from official sites
- **Pattern**: Always inherit from `BaseCrawler`, implement `crawl(year) -> List[Dict]`

### 3. Database Auto-Deduplication

`database.py` uses `UNIQUE(title, conference, year)` constraint. Re-crawling same paper updates existing record instead of duplicating.

### 4. Configuration-Driven

All conferences defined in `config.yaml`:

```yaml
conferences:
  - name: ConferenceName
    enabled: true
    years: [2023, 2024]
    description: "Full name"
```

**To add a new conference**: Just edit `config.yaml` if it's in DBLP; no code changes needed.

## Common Workflows

### Adding a New Conference (DBLP-only)

1. Edit `config.yaml` → add conference entry
2. Done! DBLP crawler auto-handles it

### Adding a Conference with Custom Scraper

1. Edit `config.yaml` → add conference
2. Add crawler class in `src/crawlers/conference_crawlers.py`:
   ```python
   class MyConfCrawler(BaseCrawler):
       def crawl(self, year: int) -> List[Dict]:
           url = f"https://conf.org/{year}"
           html = self.fetch_page(url)
           soup = self.parse_html(html)
           # Parse and return papers
   ```
3. Register in `main.py:CrawlerManager.__init__`

### Debugging Crawl Failures

1. Check `logs/crawler.log` for detailed errors
2. Common issues:
   - Missing `lxml`: Run `pip install -r requirements.txt`
   - Network errors: Check URLs in browser first
   - Empty results: DBLP URL format changed (see `DBLPCrawler.crawl()`)

### Web UI Development

- Templates in `templates/`: Use Jinja2 syntax
- Routes in `app.py`: Follow Flask patterns
- Database queries: Direct SQLite via `sqlite3` module (no ORM)

## Code Conventions

### Import Style

- Standard library → Third-party → Local modules
- Type hints used: `from typing import Dict, List, Optional`

### Error Handling

- Crawlers: Log errors but continue with next crawler
- Database: Use try-except, log failures, return False on error
- Web: Return JSON `{"success": bool, "message": str}`

### Logging

All modules use:

```python
import logging
logger = logging.getLogger(__name__)
```

Logs go to both `crawler.log` and console.

### Database Schema

**papers table**: title, authors, conference, year, abstract, pdf_url, paper_url, doi, created_at, updated_at
**crawl_history table**: Tracks each crawl attempt with status

**Database location**: `./data/papers.db` (auto-created with directory)

## Project-Specific Quirks

1. **No ORM**: Direct SQLite with `sqlite3` module. Use `conn.row_factory = sqlite3.Row` for dict-like results.

2. **Paper Dict Format**: All crawlers return `List[Dict]` where each dict must have:

   - `title`, `conference`, `year` (required)
   - `authors`, `abstract`, `pdf_url`, `paper_url`, `doi` (optional)

3. **DBLP URL Patterns**: Follow format `https://dblp.org/db/conf/{shortname}/{shortname}{year}.html`

   - NDSS: `ndss/ndss2024.html`
   - USENIX Security: `uss/uss2024.html`

4. **HTML Parsing**: Always use `BeautifulSoup(html, 'lxml')` for performance. Falls back gracefully if lxml missing (but logs error).

5. **Web UI State**: Uses URL query params for filters (no sessions). Example: `/?conference=NDSS&year=2024&page=2`

## Testing Approach

No formal test suite. Manual testing workflow:

1. Run `python main.py --conference NDSS --year 2024` to test single conference
2. Check `crawler.log` for errors
3. Verify in web UI: `python app.py` → check papers appear

## Dependencies Note

Critical dependencies:

- `lxml`: Fast HTML parsing (required by BeautifulSoup)
- `flask`: Web framework
- `pyyaml`: Config file parsing
- `requests`, `beautifulsoup4`: Web scraping

**If you see parser errors, always check if dependencies are installed first.**

## Key Files Reference

- `app.py`: Flask web app (151 lines) - START HERE for web features
- `main.py`: CLI and CrawlerManager (148 lines) - START HERE for crawling logic
- `src/models/database.py`: SQLite operations (228 lines)
- `src/crawlers/base.py`: BaseCrawler + DBLPCrawler (162 lines)
- `src/crawlers/conference_crawlers.py`: Conference-specific crawlers (~220 lines)
- `config.yaml`: All conference definitions
- `templates/*.html`: Web UI templates (Jinja2)
- `static/css/style.css`: Apple-style design system (~700 lines)

## Project Structure

```
get_paper/
├── app.py                  # Flask web application
├── main.py                 # CLI and crawler manager
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── src/                    # Source code
│   ├── models/            # Data models
│   │   └── database.py    # Database operations
│   ├── crawlers/          # Crawler implementations
│   │   ├── base.py        # BaseCrawler + DBLPCrawler
│   │   └── conference_crawlers.py  # Conference-specific
│   └── utils/             # Utility functions
├── static/                 # Web assets
│   ├── css/               # Stylesheets
│   │   └── style.css     # Apple-style design system
│   ├── js/                # JavaScript
│   └── images/            # Images
├── templates/              # Jinja2 templates
│   ├── index.html         # Paper listing
│   ├── detail.html        # Paper details
│   ├── crawl.html         # Crawl management
│   ├── statistics.html    # Statistics
│   └── config.html        # Configuration view
├── data/                   # Data files
│   └── papers.db          # SQLite database (auto-created)
├── logs/                   # Log files
│   └── crawler.log        # Crawler logs (auto-created)
└── .github/
    └── copilot-instructions.md  # This file
```

---

**When in doubt**: Check `logs/crawler.log` for errors, ensure dependencies installed, verify DBLP URLs manually in browser.
