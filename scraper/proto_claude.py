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
# Helpers
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
        print(f"'{filepath}' not found, using built-in site list.")
        return DEFAULT_RECIPE_SITES

    sites = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sites.append(line)

    if not sites:
        print(f"'{filepath}' is empty, using built-in site list.")
        return DEFAULT_RECIPE_SITES

    print(f"Loaded {len(sites)} sites from '{filepath}'")
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
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    query        TEXT    NOT NULL,
    searched_at  TEXT    NOT NULL,
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
    """
    Upsert recipes into the database.
    Returns the number of rows actually inserted/updated.
    """
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
    """Search for recipes across many sites using a generalized approach, then scrape them."""

    def __init__(self, sites_file: str = DEFAULT_SITES_FILE):
        self.recipe_sites = load_recipe_sites(sites_file)

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

    # ------------------------------------------------------------------
    # Generalised search
    # ------------------------------------------------------------------

    def search_recipe_sites_directly(self, query: str, num_results: int = 20) -> List[str]:
        """
        Generalised search: for every site in self.recipe_sites, issue a
        DuckDuckGo HTML search scoped to that domain and collect recipe URLs.
        This replaces the old per-site hard-coded scrapers and scales
        automatically as new domains are added to the sites file.
        """
        print(f"\n🔍 Searching {len(self.recipe_sites)} recipe sites for: '{query}'")

        recipe_urls: List[str] = []
        per_site = max(2, num_results // len(self.recipe_sites))

        for site in self.recipe_sites:
            urls = self._search_site_via_duckduckgo(query, site, per_site)
            recipe_urls.extend(urls)
            if urls:
                print(f"  ✓ {site}: {len(urls)} result(s)")
            # Respect DDG rate limits
            time.sleep(0.5)

        unique_urls = list(dict.fromkeys(u for u in recipe_urls if self._is_valid_recipe_url(u)))
        print(f"✓ Found {len(unique_urls)} unique recipe URLs")
        return unique_urls[:num_results]

    def _search_site_via_duckduckgo(self, query: str, site: str, limit: int) -> List[str]:
        """
        Use DuckDuckGo's HTML interface to search for `query site:<site>`.
        Returns up to `limit` URLs that belong to the given domain.
        """
        scoped_query = f"{query} site:{site}"
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(scoped_query)}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            urls = []
            for a in soup.select("a.result__url, a.result__a"):
                href = a.get("href", "")
                # DDG sometimes wraps links – extract the real URL
                href = self._unwrap_ddg_url(href)
                if not href:
                    continue
                parsed = urlparse(href)
                if site in parsed.netloc and self._is_valid_recipe_url(href):
                    clean = href.split("?")[0].rstrip("/")
                    if clean not in urls:
                        urls.append(clean)
                if len(urls) >= limit:
                    break
            return urls

        except Exception as e:
            print(f"  ⚠️  Search failed for {site}: {e}")
            return []

    @staticmethod
    def _unwrap_ddg_url(href: str) -> str:
        """DuckDuckGo sometimes returns //duckduckgo.com/l/?uddg=<encoded> links."""
        if not href:
            return ""
        if href.startswith("//duckduckgo.com/l/"):
            from urllib.parse import parse_qs, urlparse as _up
            qs = parse_qs(_up(f"https:{href}").query)
            return qs.get("uddg", [""])[0]
        if href.startswith("//"):
            return "https:" + href
        return href

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
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
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

    def search_and_scrape(
        self,
        query: str,
        num_results: int = 20,
        db_path: str = "recipes.db",
    ) -> str:
        """
        Full pipeline: search → scrape → save to SQLite.
        Returns the path to the database file.
        """
        urls = self.search_recipe_sites_directly(query, num_results)
        if not urls:
            print("⚠️  No recipe URLs found!")
            return db_path

        recipes = self.scrape_multiple(urls, delay=1.5)
        if not recipes:
            print("⚠️  No recipes successfully scraped!")
            return db_path

        save_recipes_to_db(recipes, query, db_path)
        return db_path


# ---------------------------------------------------------------------------
# Entry point — accepts a query from the command line or prompts the user
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("🍳  RECIPE SEARCH & SCRAPER")
    print("=" * 60)

    # Accept query from CLI argument or interactive prompt
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
    print(f"✓ Done!  Results saved to: {db}")
    print("  Query the DB with:  sqlite3 recipes.db 'SELECT title, source_site FROM recipes;'")
    print("=" * 60)