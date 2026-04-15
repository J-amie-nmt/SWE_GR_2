# recipe_search_scraper.py
"""
Recipe Search & Scraper
Searches for recipes across multiple websites and stores data in SQLite database.

Usage:
    python recipe_search_scraper.py                    # interactive prompt
    python recipe_search_scraper.py "pasta carbonara"  # direct query arg
"""

from recipe_scrapers import scrape_html
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import time
from typing import List, Dict, Optional
from datetime import datetime
import re
import sys
import os


# ---------------------------------------------------------------------------
# Generic search URL patterns
#
# For each site we try both common search URL formats.
# No per-site config needed — adding a domain to website-recipe-list.txt
# is all that's required to support a new site.
# ---------------------------------------------------------------------------

SEARCH_URL_PATTERNS = [
    "https://www.{domain}/search?q={query}",
    "https://www.{domain}/search/{query}",
]

# Generic heuristic: hrefs that look like recipe content pages.
# Avoids navigation, search, tag, author, and other non-recipe pages.
RECIPE_PATH_SIGNALS = ["/recipe/", "/recipes/"]
NON_RECIPE_PATTERNS = [
    "/search", "/tag/", "/tags/", "/author/", "/category/",
    "/collections/", "/gallery/", "/how-to/", "/article/",
    "/news/", "/video/", "/podcast/", "/shop/", "/review/",
]

def _is_recipe_link(href: str, domain: str) -> bool:
    """
    Return True if `href` looks like a recipe page on `domain`.
    Checks that:
      1. The URL belongs to the expected domain.
      2. The path contains a known recipe signal (/recipe/ or /recipes/).
      3. The path does not match non-recipe patterns.
      4. The slug is reasonably long (avoids bare /recipes/ index pages).
    """
    if domain not in href:
        return False
    parsed_path = urlparse(href).path.rstrip("/")
    if not any(signal in parsed_path for signal in RECIPE_PATH_SIGNALS):
        return False
    if any(bad in parsed_path for bad in NON_RECIPE_PATTERNS):
        return False
    # Must have meaningful content after the /recipe(s)/ segment
    parts = [p for p in parsed_path.split("/") if p]
    recipe_idx = next((i for i, p in enumerate(parts) if p in ("recipe", "recipes")), None)
    if recipe_idx is None or recipe_idx >= len(parts) - 1:
        return False
    return True


# ---------------------------------------------------------------------------
# Site list loader
# ---------------------------------------------------------------------------

DEFAULT_SITES_FILE = "website-recipe-list.txt"

DEFAULT_RECIPE_SITES = [
    "allrecipes.com",
    "foodnetwork.com",
    "bonappetit.com",
    "epicurious.com",
    "seriouseats.com",
    "tasty.co",
    "simplyrecipes.com",
    "delish.com",
    "thekitchn.com",
    "food52.com",
]


def load_recipe_sites(filepath: str = DEFAULT_SITES_FILE) -> List[str]:
    """
    Load recipe site list from a plain-text file (one domain per line).
    Falls back to the built-in list if the file is missing or empty.
    Lines starting with '#' are treated as comments and ignored.
    """
    if not os.path.exists(filepath):
        print(f"ℹ️  '{filepath}' not found — using built-in site list.")
        return DEFAULT_RECIPE_SITES

    sites = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sites.append(line)

    if not sites:
        print(f"⚠️  No usable sites in '{filepath}' — using built-in site list.")
        return DEFAULT_RECIPE_SITES

    print(f"✓ Loaded {len(sites)} sites from '{filepath}'")
    return sites


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    url           TEXT    UNIQUE NOT NULL,
    author        TEXT,
    source_site   TEXT,
    image_url     TEXT,
    total_time    TEXT,
    yields        TEXT,
    cuisine       TEXT,
    category      TEXT,
    calories      TEXT,
    dietary_tags  TEXT,
    ingredients   TEXT,
    instructions  TEXT,
    scraped_date  TEXT
);

CREATE TABLE IF NOT EXISTS search_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    query         TEXT    NOT NULL,
    searched_at   TEXT    NOT NULL,
    results_found INTEGER
);
"""


def get_db_connection(db_path: str = "recipes.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(DB_SCHEMA)
    conn.commit()
    return conn


def save_recipes_to_db(recipes: List[Dict], query: str, db_path: str = "recipes.db") -> int:
    """Upsert recipes into the database. Returns the number of rows inserted/updated."""
    if not recipes:
        print("⚠️  No recipes to save!")
        return 0

    conn = get_db_connection(db_path)
    saved = 0

    with conn:
        for r in recipes:
            try:
                conn.execute(
                    """
                    INSERT INTO recipes
                        (title, url, author, source_site, image_url, total_time,
                         yields, cuisine, category, calories, dietary_tags,
                         ingredients, instructions, scraped_date)
                    VALUES
                        (:title, :url, :author, :source_site, :image_url, :total_time,
                         :yields, :cuisine, :category, :calories, :dietary_tags,
                         :ingredients, :instructions, :scraped_date)
                    ON CONFLICT(url) DO UPDATE SET
                        title        = excluded.title,
                        author       = excluded.author,
                        image_url    = excluded.image_url,
                        total_time   = excluded.total_time,
                        yields       = excluded.yields,
                        cuisine      = excluded.cuisine,
                        category     = excluded.category,
                        calories     = excluded.calories,
                        dietary_tags = excluded.dietary_tags,
                        ingredients  = excluded.ingredients,
                        instructions = excluded.instructions,
                        scraped_date = excluded.scraped_date
                    """,
                    r,
                )
                saved += 1
            except sqlite3.Error as e:
                print(f"⚠️  DB error for '{r.get('title', r['url'])}': {e}")

        conn.execute(
            "INSERT INTO search_log (query, searched_at, results_found) VALUES (?, ?, ?)",
            (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), saved),
        )

    conn.close()
    print(f"\n💾 Saved {saved} recipes to '{db_path}'")
    return saved



# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

class RecipeSearchScraper:
    """Search for recipes using each site's own search URL, then scrape them."""

    def __init__(self, sites_file: str = DEFAULT_SITES_FILE, db_path: str = "recipes.db"):
        self.recipe_sites = load_recipe_sites(sites_file)
        self.db_path = db_path
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_recipe_sites_directly(self, query: str, num_results: int = 20) -> List[str]:
        """
        For every site in self.recipe_sites, fetch that site's own search results
        page and extract recipe links using the site-specific link_filter.
        No third-party search engine involved — zero rate-limit risk.
        """
        print(f"\n🔍 Searching {len(self.recipe_sites)} recipe sites for: '{query}'")

        recipe_urls: List[str] = []
        per_site = max(2, num_results // len(self.recipe_sites))

        for site in self.recipe_sites:
            urls = self._search_one_site(query, site, per_site)
            recipe_urls.extend(urls)
            status = f"✓ {len(urls)} result(s)" if urls else "✗ 0 results"
            print(f"  {status} — {site}")
            time.sleep(0.75)  # polite delay between sites

        unique_urls = list(dict.fromkeys(u for u in recipe_urls if self._is_valid_recipe_url(u)))
        print(f"✓ Found {len(unique_urls)} unique recipe URLs")
        return unique_urls[:num_results]

    def _search_one_site(self, query: str, site: str, limit: int) -> List[str]:
        """
        Try both generic search URL patterns for `site` and return up to `limit`
        recipe URLs. Stops as soon as one pattern yields results.
        Silently skips sites that return errors or block the request.
        """
        encoded = quote_plus(query)
        candidate_urls = [
            pattern.format(domain=site, query=encoded)
            for pattern in SEARCH_URL_PATTERNS
        ]

        for search_url in candidate_urls:
            urls = self._fetch_recipe_links(search_url, site, limit)
            if urls:
                return urls  # First working pattern wins

        return []

    def _fetch_recipe_links(self, search_url: str, site: str, limit: int) -> List[str]:
        """
        Fetch `search_url`, parse the HTML, and return links that pass the
        generic recipe URL heuristic for `site`.
        Returns an empty list on any error (4xx, 5xx, timeout, etc.).
        """
        try:
            response = requests.get(search_url, headers=self.headers, timeout=12)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            urls = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Resolve relative URLs
                if href.startswith("/"):
                    href = f"https://www.{site}{href}"
                elif not href.startswith("http"):
                    continue

                href = href.split("?")[0].rstrip("/")

                if _is_recipe_link(href, site) and href not in urls:
                    urls.append(href)

                if len(urls) >= limit:
                    break

            return urls

        except requests.exceptions.RequestException:
            return []

    # ------------------------------------------------------------------
    # URL validation
    # ------------------------------------------------------------------

    def _is_valid_recipe_url(self, url: str) -> bool:
        if not url.startswith("http"):
            return False

        invalid_patterns = [
            "google.com", "youtube.com", "pinterest.com", "facebook.com",
            "/search", "/category", "/tag", "/author", "/collections", "/gallery",
        ]
        if any(p in url.lower() for p in invalid_patterns):
            return False

        domain = urlparse(url).netloc
        return any(site in domain for site in self.recipe_sites)

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """Fetch and parse a single recipe URL. Returns None on any failure."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"  ✗ HTTP {response.status_code}: {url}")
                return None

            scraper = scrape_html(html=response.content, org_url=url)

            return {
                "title":        scraper.title(),
                "url":          url,
                "author":       self._safe(scraper.author) or "Unknown",
                "image_url":    self._safe(scraper.image) or "",
                "total_time":   self._format_time(self._safe(scraper.total_time)),
                "yields":       self._safe(scraper.yields) or "",
                "cuisine":      self._safe(scraper.cuisine) or "",
                "category":     self._safe(scraper.category) or "",
                "ingredients":  " | ".join(scraper.ingredients()),
                "instructions": self._clean_instructions(self._safe(scraper.instructions)),
                "calories":     self._extract_calories(scraper),
                "dietary_tags": ", ".join(self._extract_dietary_tags(scraper)),
                "source_site":  urlparse(url).netloc,
                "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except requests.exceptions.HTTPError as e:
            print(f"  ✗ HTTP error scraping {url}: {e}")
            return None

        except Exception as e:
            print(f"  ✗ Failed to scrape {url}: {e}")
            return None

    def _safe(self, method):
        try:
            return method()
        except Exception:
            return None

    def _format_time(self, val) -> str:
        if not val:
            return ""
        return f"{val} minutes" if isinstance(val, int) else str(val)

    def _clean_instructions(self, text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"\s+", " ", text).replace("\n\n", " | ").strip()
        return cleaned[:2000] + "..." if len(cleaned) > 2000 else cleaned

    def _extract_calories(self, scraper) -> str:
        try:
            nutrients = scraper.nutrients()
            cal = nutrients.get("calories", "")
            return str(cal).replace("calories", "").strip() if cal else ""
        except Exception:
            return ""

    def _extract_dietary_tags(self, scraper) -> List[str]:
        tags = []
        try:
            ingredients = scraper.ingredients()
            text = " ".join(ingredients).lower()
            if self._is_vegan(ingredients):
                tags.append("vegan")
            elif self._is_vegetarian(ingredients):
                tags.append("vegetarian")
            for label, keywords in [
                ("gluten-free", ["gluten-free", "gluten free"]),
                ("dairy-free",  ["dairy-free", "dairy free"]),
                ("keto",        ["keto", "low-carb", "low carb"]),
                ("paleo",       ["paleo"]),
            ]:
                if any(kw in text for kw in keywords):
                    tags.append(label)
        except Exception:
            pass
        return tags

    def _is_vegan(self, ingredients: List[str]) -> bool:
        non_vegan = ["meat", "chicken", "beef", "pork", "fish", "egg",
                     "milk", "cheese", "butter", "cream", "honey", "bacon",
                     "sausage", "turkey", "lamb", "yogurt", "gelatin"]
        text = " ".join(ingredients).lower()
        return not any(w in text for w in non_vegan)

    def _is_vegetarian(self, ingredients: List[str]) -> bool:
        non_veg = ["meat", "chicken", "beef", "pork", "fish", "bacon",
                   "sausage", "turkey", "lamb", "anchovy", "shrimp",
                   "crab", "lobster", "clam", "oyster"]
        text = " ".join(ingredients).lower()
        return not any(w in text for w in non_veg)

    def scrape_multiple(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        recipes = []
        total = len(urls)
        print(f"\n📥 Scraping {total} recipes…")

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] {url}")
            recipe = self.scrape_recipe(url)
            if recipe:
                recipes.append(recipe)
                print(f"  ✓ {recipe['title']}")
            if i < total:
                time.sleep(delay)

        print(f"\n✓ Successfully scraped {len(recipes)}/{total} recipes")
        return recipes

    # ------------------------------------------------------------------
    # Full workflow
    # ------------------------------------------------------------------

    def search_and_scrape(self, query: str, num_results: int = 20) -> str:
        """Full pipeline: search → scrape → save to SQLite. Returns the DB path."""
        urls = self.search_recipe_sites_directly(query, num_results)
        if not urls:
            print("⚠️  No recipe URLs found!")
            return self.db_path

        recipes = self.scrape_multiple(urls, delay=1.5)
        if not recipes:
            print("⚠️  No recipes successfully scraped!")
            return self.db_path

        save_recipes_to_db(recipes, query, self.db_path)
        return self.db_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("🍳  RECIPE SEARCH & SCRAPER")
    print("=" * 60)

    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        print(f"\nUsing query from command line: '{user_query}'")
    else:
        user_query = input("\nEnter a recipe search query (e.g. 'chocolate chip cookies'): ").strip()
        if not user_query:
            print("No query entered. Exiting.")
            sys.exit(0)

    num = input("How many recipes to fetch? [default: 15]: ").strip()
    num_results = int(num) if num.isdigit() else 15

    scraper = RecipeSearchScraper(sites_file=DEFAULT_SITES_FILE)
    db = scraper.search_and_scrape(query=user_query, num_results=num_results)

    print("\n" + "=" * 60)
    print(f"✓ Done! Results saved to: {db}")
    print("  View results: sqlite3 recipes.db 'SELECT title, source_site FROM recipes;'")
    print("=" * 60)