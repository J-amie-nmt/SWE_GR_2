# scraper_v2.py
"""
Recipe Search & Scraper
Searches for recipes across multiple websites and stores data in Supabase.

Usage (interactive):
    python scraper_v2.py

Dependencies:
    pip install recipe-scrapers beautifulsoup4 requests lxml supabase
"""

from recipe_scrapers import scrape_html
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import quote_plus, urlparse
import time
from typing import List, Dict, Optional, Set
from datetime import datetime
import re
import warnings
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase import create_client, Client

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")  # use service role key for scraper


# ═══════════════════════════════════════════════════════════════
#  SITE LIST
# ═══════════════════════════════════════════════════════════════

all_recipes_sites = [
    '101cookbooks.com', 'acouplecooks.com', 'acozykitchen.com', 'addapinch.com',
    'africanbites.com', 'alexandracooks.com', 'allrecipes.com', 'allthehealthythings.com',
    'altonbrown.com', 'ambitiouskitchen.com', 'americastestkitchen.com',
    'averiecooks.com', 'barefeetinthekitchen.com', 'barefootcontessa.com',
    'bbc.co.uk', 'bbcgoodfood.com', 'bellyfull.net', 'bettycrocker.com',
    'biggerbolderbaking.com', 'bigoven.com', 'bonappetit.com', 'bowlofdelicious.com',
    'budgetbytes.com', 'cafedelites.com', 'carlsbadcravings.com', 'cdkitchen.com',
    'chefkoch.de', 'chefsavvy.com', 'closetcooking.com', 'cookieandkate.com',
    'cooking.nytimes.com', 'cookingclassy.com', 'copykat.com', 'countryliving.com',
    'damndelicious.net', 'davidlebovitz.com', 'delish.com', 'dinneratthezoo.com',
    'downshiftology.com', 'eatingbirdfood.com', 'eatingwell.com', 'epicurious.com',
    'errenskitchen.com', 'familyfoodonthetable.com', 'feastingathome.com',
    'feelgoodfoodie.net', 'fifteenspatulas.com', 'food.com', 'food52.com',
    'foodandwine.com', 'foodnetwork.com', 'forksoverknives.com', 'gimmesomeoven.com',
    'goodhousekeeping.com', 'halfbakedharvest.com', 'handletheheat.com',
    'hellofresh.com', 'houseofnasheats.com', 'iambaker.net', 'insanelygoodrecipes.com',
    'inspiredtaste.net', 'jamieoliver.com', 'jocooks.com', 'joshuaweissman.com',
    'joyfoodsunshine.com', 'justonecookbook.com', 'kingarthurbaking.com',
    'kitchensanctuary.com', 'kristineskitchenblog.com', 'laurenslatest.com',
    'lazycatkitchen.com', 'lecremedelacrumb.com', 'loveandlemons.com', 'maangchi.com',
    'marmiton.org', 'marthastewart.com', 'minimalistbaker.com', 'ministryofcurry.com',
    'momontimeout.com', 'mybakingaddiction.com', 'natashaskitchen.com',
    'noracooks.com', 'ohsheglows.com', 'omnivorescookbook.com', 'onceuponachef.com',
    'ourbestbites.com', 'pinchofyum.com', 'preppykitchen.com', 'rainbowplantlife.com',
    'recipetineats.com', 'sallysbakingaddiction.com', 'saveur.com', 'seriouseats.com',
    'simplyrecipes.com', 'sipandfeast.com', 'skinnytaste.com', 'southernliving.com',
    'spendwithpennies.com', 'tasteofhome.com', 'tastesbetterfromscratch.com',
    'tasty.co', 'themediterraneandish.com', 'therecipecritic.com',
    'thespruceeats.com', 'thewoksoflife.com', 'twopeasandtheirpod.com',
    'wellplated.com', 'whatsgabycooking.com', 'wholefoodsmarket.com', 'yummly.com',
]


# ═══════════════════════════════════════════════════════════════
#  SITE SEARCH CONFIGS
# ═══════════════════════════════════════════════════════════════

SITE_SEARCH_CONFIGS = {
    'cooking.nytimes.com': {
        'search_url': 'https://cooking.nytimes.com/search?q={query}',
        'recipe_path_re': r'/recipes/\d+',
    },
    'bonappetit.com': {
        'search_url': 'https://www.bonappetit.com/search?q={query}',
        'recipe_path_re': r'/recipe/[a-z0-9-]+$',
    },
    'epicurious.com': {
        'search_url': 'https://www.epicurious.com/search/{query}',
        'recipe_path_re': r'/recipes/food/views/',
    },
    'food52.com': {
        'search_url': 'https://food52.com/search?q={query}',
        'recipe_path_re': r'/recipes/\d+',
    },
    'seriouseats.com': {
        'search_url': 'https://www.seriouseats.com/search?q={query}',
        'recipe_path_re': r'seriouseats\.com/(?!search|category|author|tag)[a-z0-9-]+-recipe',
    },
    'allrecipes.com': {
        'search_url': 'https://www.allrecipes.com/search?q={query}',
        'recipe_path_re': r'/recipe/\d+/',
    },
    'foodnetwork.com': {
        'search_url': 'https://www.foodnetwork.com/search/{query}-',
        'recipe_path_re': r'/recipes/[^/]+/[^/]+-recipe-\d+',
    },
    'tasty.co': {
        'search_url': 'https://tasty.co/search?q={query}',
        'recipe_path_re': r'/recipe/[a-z0-9-]+$',
    },
    'bbcgoodfood.com': {
        'search_url': 'https://www.bbcgoodfood.com/search?q={query}',
        'recipe_path_re': r'/recipes/(?!category|collection|glossary)[a-z0-9-]+$',
    },
    'jamieoliver.com': {
        'search_url': 'https://www.jamieoliver.com/search/?s={query}',
        'recipe_path_re': r'/recipes/[^/]+/[a-z0-9-]+/?$',
    },
    'marmiton.org': {
        'search_url': 'https://www.marmiton.org/recettes/recherche.aspx?aqt={query}',
        'recipe_path_re': r'/recettes/recette_',
    },
    'chefkoch.de': {
        'search_url': 'https://www.chefkoch.de/suche.php?suche={query}',
        'recipe_path_re': r'/rezepte/\d+/',
    },
    'delish.com': {
        'search_url': 'https://www.delish.com/search/?q={query}',
        'recipe_path_re': r'/cooking/recipe-ideas/[a-z0-9-]+$',
    },
    'americastestkitchen.com': {
        'search_url': 'https://www.americastestkitchen.com/search?q={query}',
        'recipe_path_re': r'/recipes/\d+',
    },
    'bettycrocker.com': {
        'search_url': 'https://www.bettycrocker.com/search#q={query}&t=recipe',
        'recipe_path_re': r'/recipes/[a-z0-9-]+/[a-z0-9-]+-\d+',
    },
    'kingarthurbaking.com': {
        'search_url': 'https://www.kingarthurbaking.com/search?q={query}',
        'recipe_path_re': r'/recipes/[a-z0-9-]+-recipe$',
    },
}

DEFAULT_CONFIG = {
    'search_url': 'https://www.{site}/search?q={query}',
    'recipe_path_re': r'/recipes?/(?!category|tag|author|collection|index|search|browse|list|ideas)[a-z0-9][a-z0-9_-]{3,}/?$',
}

LISTING_PATH_SEGMENTS = {
    'category', 'categories', 'tag', 'tags', 'author', 'authors',
    'collection', 'collections', 'index', 'browse', 'archive',
    'search', 'list', 'gallery', 'topic', 'cuisine', 'meal-type',
    'ingredient', 'how-to', 'technique',
}

PERMANENT_FAILURE_CODES = {402, 403, 406, 429}


# ═══════════════════════════════════════════════════════════════
#  SUPABASE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def save_recipe(supabase: Client, recipe: Dict) -> bool:
    """
    Insert a recipe. Skips duplicates by checking URL first.
    Returns True if inserted, False if duplicate.
    """
    existing = supabase.table("recipes").select("id").eq("url", recipe["url"]).execute()
    if existing.data:
        return False

    # Map nutrient keys to match Supabase column names
    row = {
        "title":                   recipe.get("title"),
        "url":                     recipe.get("url"),
        "author":                  recipe.get("author"),
        "source_site":             recipe.get("source_site"),
        "image_url":               recipe.get("image_url"),
        "total_time":              recipe.get("total_time"),
        "yields":                  recipe.get("yields"),
        "cuisine":                 recipe.get("cuisine"),
        "category":                recipe.get("category"),
        "calories":                recipe.get("calories"),
        "fat_content":             recipe.get("fatContent"),
        "saturated_fat_content":   recipe.get("saturatedFatContent"),
        "trans_fat_content":       recipe.get("transFatContent"),
        "unsaturated_fat_content": recipe.get("unsaturatedFatContent"),
        "carbohydrate_content":    recipe.get("carbohydrateContent"),
        "sugar_content":           recipe.get("sugarContent"),
        "fiber_content":           recipe.get("fiberContent"),
        "protein_content":         recipe.get("proteinContent"),
        "sodium_content":          recipe.get("sodiumContent"),
        "cholesterol_content":     recipe.get("cholesterolContent"),
        "dietary_tags":            recipe.get("dietary_tags"),
        "ingredients":             recipe.get("ingredients"),
        "instructions":            recipe.get("instructions"),
        "scraped_date":            recipe.get("scraped_date"),
    }

    supabase.table("recipes").insert(row).execute()
    return True


def log_search(supabase: Client, query: str, sites: Optional[List[str]], results: int):
    supabase.table("search_log").insert({
        "query":          query,
        "sites_used":     ','.join(sites) if sites else 'all',
        "results_found":  results,
        "searched_at":    datetime.now().isoformat(),
    }).execute()


def list_recipes(supabase: Client, limit: int = 50):
    rows = supabase.table("recipes") \
        .select("id, title, source_site, cuisine, dietary_tags, scraped_date") \
        .order("id", desc=True) \
        .limit(limit) \
        .execute().data

    if not rows:
        print("  (no recipes saved yet)")
        return

    print(f"\n  {'ID':<5} {'Title':<45} {'Site':<24} {'Cuisine':<15} Dietary Tags")
    print("  " + "─" * 110)
    for r in rows:
        print(
            f"  {r['id']:<5} {str(r['title'])[:44]:<45} "
            f"{str(r['source_site'] or '')[:23]:<24} "
            f"{str(r['cuisine'] or '')[:14]:<15} "
            f"{str(r['dietary_tags'] or '')[:30]}"
        )
    total = supabase.table("recipes").select("id", count="exact").execute().count
    print(f"\n  Showing {len(rows)} of {total} saved recipe(s).")


def view_recipe(supabase: Client, recipe_id: int):
    rows = supabase.table("recipes").select("*").eq("id", recipe_id).execute().data
    if not rows:
        print(f"  No recipe with ID {recipe_id}.")
        return
    r = rows[0]
    print(f"\n  {'═'*60}")
    print(f"  {r['title']}")
    print(f"  {'═'*60}")
    print(f"  Author    : {r['author'] or 'Unknown'}")
    print(f"  Site      : {r['source_site']}")
    print(f"  URL       : {r['url']}")
    print(f"  Time      : {r['total_time'] or 'N/A'}   |   Yields: {r['yields'] or 'N/A'}")
    print(f"  Cuisine   : {r['cuisine'] or 'N/A'}   |   Category: {r['category'] or 'N/A'}")
    print(f"  Dietary   : {r['dietary_tags'] or 'N/A'}")

    print(f"\n  📋 INGREDIENTS")
    for i, ing in enumerate((r['ingredients'] or '').split(' | '), 1):
        if ing.strip():
            print(f"     {i:>2}. {ing.strip()}")

    print(f"\n  📝 INSTRUCTIONS")
    for i, step in enumerate((r['instructions'] or '').split(' | '), 1):
        if step.strip():
            text = step.strip()[:220] + ('…' if len(step.strip()) > 220 else '')
            print(f"     Step {i}: {text}")

    nutrient_cols = [
        ('calories', 'Calories'), ('fat_content', 'Fat'),
        ('carbohydrate_content', 'Carbs'), ('protein_content', 'Protein'),
        ('sodium_content', 'Sodium'), ('sugar_content', 'Sugar'),
        ('fiber_content', 'Fiber'), ('cholesterol_content', 'Cholesterol'),
    ]
    nutrition_lines = [(label, r[col]) for col, label in nutrient_cols if r.get(col)]
    if nutrition_lines:
        print(f"\n  🥗 NUTRITION")
        for label, val in nutrition_lines:
            print(f"     {label}: {val}")
    print()


# ═══════════════════════════════════════════════════════════════
#  SCRAPER CLASS
# ═══════════════════════════════════════════════════════════════

class RecipeSearchScraper:
    NUTRIENT_KEYS = [
        'calories', 'fatContent', 'saturatedFatContent', 'transFatContent',
        'unsaturatedFatContent', 'carbohydrateContent', 'sugarContent',
        'fiberContent', 'proteinContent', 'sodiumContent', 'cholesterolContent',
    ]

    def __init__(self):
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self._blocked_sites: Set[str] = set()
        self.supabase = get_supabase()
        print("  ✅ Connected to Supabase")

    def _get_site_config(self, site: str) -> dict:
        config = SITE_SEARCH_CONFIGS.get(site, {})
        search_url = config.get('search_url', DEFAULT_CONFIG['search_url'].replace('{site}', site))
        recipe_path_re = config.get('recipe_path_re', DEFAULT_CONFIG['recipe_path_re'])
        return {'search_url': search_url, 'recipe_path_re': recipe_path_re}

    def _is_recipe_url(self, href: str, site: str, recipe_path_re: str) -> bool:
        if not re.search(recipe_path_re, href, re.IGNORECASE):
            return False
        path = urlparse(href).path.lower().strip('/')
        segments = set(path.split('/'))
        return not (segments & LISTING_PATH_SEGMENTS)

    def _search_site(self, site: str, query: str, limit: int = 6) -> List[str]:
        if site in self._blocked_sites:
            return []
        config = self._get_site_config(site)
        search_url = config['search_url'].replace('{query}', quote_plus(query))
        recipe_path_re = config['recipe_path_re']
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code in PERMANENT_FAILURE_CODES:
                self._blocked_sites.add(site)
            return []
        except Exception:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        urls: List[str] = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/'):
                href = f"https://{'www.' if not site.startswith('www') else ''}{site}{href}"
            if site not in href:
                continue
            clean_url = href.split('?')[0].rstrip('/')
            if self._is_recipe_url(clean_url, site, recipe_path_re):
                if clean_url not in urls:
                    urls.append(clean_url)
                if len(urls) >= limit:
                    break
        if urls:
            print(f"    ✓ {site}: {len(urls)} recipe(s)")
        return urls

    def search_recipe_sites_directly(
        self,
        query: str,
        num_results: int = 20,
        sites: Optional[List[str]] = None,
        max_workers: int = 10,
        per_site_limit: int = 6,
    ) -> List[str]:
        target_sites = sites if sites is not None else all_recipes_sites
        print(f"\n🔍 Searching {len(target_sites)} recipe site(s) for: '{query}'")
        recipe_urls: List[str] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_site = {
                executor.submit(self._search_site, site, query, per_site_limit): site
                for site in target_sites
            }
            for future in as_completed(future_to_site):
                recipe_urls.extend(future.result())
        unique_urls = list(dict.fromkeys(recipe_urls))
        if self._blocked_sites:
            print(f"  ℹ️  {len(self._blocked_sites)} site(s) blocked/paywalled (skipped)")
        print(f"✓ Found {len(unique_urls)} unique recipe URL(s)")
        return unique_urls if num_results is None else unique_urls[:num_results]

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            scraper = scrape_html(html=response.content, org_url=url)
            recipe_data = {
                'title':        scraper.title(),
                'url':          url,
                'author':       self._safe_extract(scraper.author) or 'Unknown',
                'image_url':    self._safe_extract(scraper.image) or '',
                'total_time':   self._format_time(self._safe_extract(scraper.total_time)),
                'yields':       self._safe_extract(scraper.yields) or '',
                'cuisine':      self._safe_extract(scraper.cuisine) or '',
                'category':     self._safe_extract(scraper.category) or '',
                'ingredients':  ' | '.join(scraper.ingredients()),
                'instructions': self._clean_instructions(self._safe_extract(scraper.instructions)),
                **self._extract_nutrients(scraper),
                'dietary_tags': ', '.join(self._extract_dietary_tags(scraper)),
                'source_site':  urlparse(url).netloc,
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            return recipe_data
        except Exception as e:
            print(f"  ✗ Failed to scrape {url}: {e}")
            return None

    def _safe_extract(self, method):
        try:
            return method()
        except Exception:
            return None

    def _format_time(self, time_val) -> str:
        if not time_val:
            return ''
        return f"{time_val} minutes" if isinstance(time_val, int) else str(time_val)

    def _clean_instructions(self, instructions: Optional[str]) -> str:
        if not instructions:
            return ''
        cleaned = re.sub(r'\s+', ' ', instructions).replace('\n\n', ' | ').strip()
        return cleaned[:2000] + '...' if len(cleaned) > 2000 else cleaned

    def _extract_nutrients(self, scraper) -> Dict[str, str]:
        result = {k: '' for k in self.NUTRIENT_KEYS}
        try:
            raw = scraper.nutrients()
            if raw:
                for key, val in raw.items():
                    result[key] = str(val).strip()
        except Exception:
            pass
        return result

    def _extract_dietary_tags(self, scraper) -> List[str]:
        tags = []
        try:
            ingredients = scraper.ingredients()
            text = ' '.join(ingredients).lower()
            if self._is_vegan(ingredients):
                tags.append('vegan')
            elif self._is_vegetarian(ingredients):
                tags.append('vegetarian')
            if 'gluten-free' in text or 'gluten free' in text:
                tags.append('gluten-free')
            if 'dairy-free' in text or 'dairy free' in text:
                tags.append('dairy-free')
            if any(w in text for w in ['keto', 'low-carb', 'low carb']):
                tags.append('keto')
            if 'paleo' in text:
                tags.append('paleo')
        except Exception:
            pass
        return tags

    def _is_vegan(self, ingredients: List[str]) -> bool:
        non_vegan = {'meat','chicken','beef','pork','fish','egg','milk','cheese',
                     'butter','cream','honey','bacon','sausage','turkey','lamb',
                     'yogurt','gelatin'}
        text = ' '.join(ingredients).lower()
        return not any(item in text for item in non_vegan)

    def _is_vegetarian(self, ingredients: List[str]) -> bool:
        non_veg = {'meat','chicken','beef','pork','fish','bacon','sausage',
                   'turkey','lamb','anchovy','shrimp','crab','lobster','clam','oyster'}
        text = ' '.join(ingredients).lower()
        return not any(item in text for item in non_veg)

    def scrape_multiple(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        recipes = []
        total = len(urls)
        print(f"\n📥 Scraping {total} recipe(s)...")
        for i, url in enumerate(urls, 1):
            print(f"  [{i}/{total}] {url}")
            recipe = self.scrape_recipe(url)
            if recipe:
                recipes.append(recipe)
                print(f"  ✓ {recipe['title']}")
            if i < total:
                time.sleep(delay)
        print(f"\n✓ Scraped {len(recipes)}/{total} successfully")
        return recipes

    def save_to_db(self, recipes: List[Dict]) -> int:
        if not recipes:
            print("⚠️  No recipes to save!")
            return 0
        inserted = 0
        for recipe in recipes:
            if save_recipe(self.supabase, recipe):
                inserted += 1
        skipped = len(recipes) - inserted
        print(f"\n💾 Saved {inserted} new recipe(s) to Supabase"
              + (f"  ({skipped} duplicate(s) skipped)" if skipped else ""))
        return inserted

    def search_and_scrape(
        self,
        query: str,
        num_results: int = None,
        sites: Optional[List[str]] = None,
        max_workers: int = 10,
        scrape_delay: float = 1.5,
    ) -> int:
        urls = self.search_recipe_sites_directly(
            query, num_results=num_results, sites=sites, max_workers=max_workers,
        )
        if not urls:
            print("⚠️  No recipe URLs found!")
            return 0
        recipes = self.scrape_multiple(urls, delay=scrape_delay)
        if not recipes:
            print("⚠️  No recipes successfully scraped!")
            return 0
        saved = self.save_to_db(recipes)
        log_search(self.supabase, query, sites, saved)
        return saved


# ═══════════════════════════════════════════════════════════════
#  INTERACTIVE CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🍳 RECIPE SEARCH & SCRAPER  (Supabase edition)")
    print("=" * 60)

    scraper = RecipeSearchScraper()

    while True:
        print()
        print("Actions:  [1] Search & scrape   [2] List saved   [3] View recipe   [q] Quit")
        action = input("Choice: ").strip().lower()

        if action in ("q", "quit", "exit"):
            print("Bye!")
            break

        elif action == "2":
            raw = input("Max rows to show [default 50]: ").strip()
            limit = int(raw) if raw.isdigit() else 50
            list_recipes(scraper.supabase, limit)

        elif action == "3":
            raw = input("Recipe ID: ").strip()
            if raw.isdigit():
                view_recipe(scraper.supabase, int(raw))
            else:
                print("  Please enter a numeric ID.")

        elif action == "1":
            query = input("Search query: ").strip()
            if not query:
                print("  Please enter a search term.")
                continue

            print("\nSearch scope:  [1] All sites (default)   [2] Specific sites")
            scope = input("Choice [1/2]: ").strip() or "1"
            sites = None
            if scope == "2":
                raw = input("Sites (comma-separated, e.g. allrecipes.com,food.com): ").strip()
                sites = [s.strip() for s in raw.split(",") if s.strip()] or None

            raw_limit = input("Max recipes to scrape [blank = all found]: ").strip()
            num_results = None
            if raw_limit:
                try:
                    num_results = max(1, int(raw_limit))
                except ValueError:
                    print("  Invalid number — scraping all found.")

            raw_delay = input("Delay between requests in seconds [default 1.5]: ").strip()
            scrape_delay = 1.5
            if raw_delay:
                try:
                    scrape_delay = max(0.0, float(raw_delay))
                except ValueError:
                    print("  Invalid delay — using 1.5s.")

            saved = scraper.search_and_scrape(
                query=query,
                num_results=num_results,
                sites=sites,
                scrape_delay=scrape_delay,
            )
            if saved:
                print(f"\n✅  Done!  {saved} recipe(s) saved.")

        else:
            print("  Unrecognised choice — please enter 1, 2, 3, or q.")

        again = input("\nReturn to menu? [Y/n]: ").strip().lower()
        if again in ("n", "no"):
            print("Bye!")
            break
