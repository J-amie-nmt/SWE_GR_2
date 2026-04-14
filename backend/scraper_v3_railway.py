# scraper_v3_railway.py
"""
Recipe Search & Scraper
Searches for recipes across multiple websites and stores data in Supabase.

Usage (interactive):
    python3 scraper_v3_railway.py

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
DEFAULT_SITES_FILE = "website-recipe-list.txt"

# ═══════════════════════════════════════════════════════════════
#  SITE LIST
# ═══════════════════════════════════════════════════════════════

# Fallback list of recipe websites
# (in case load function fails / file is not found)
DEFAULT_RECIPE_SITES = [
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

def load_recipe_sites(filepath: str = DEFAULT_SITES_FILE) -> List[str]:
    """
    Load recipe site list from a plain-text file (one domain per line).
    Lines starting with '#' are treated as comments and ignored.
    """
    if not os.path.exists(filepath):
        return DEFAULT_RECIPE_SITES

    sites = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sites.append(line)

    if not sites:
        return DEFAULT_RECIPE_SITES

    print(f"Loaded {len(sites)} sites from '{filepath}'")
    return sites


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
    # FIX 1: consistent lowercase table name "recipes" everywhere
    existing = supabase.table("Recipes").select("id").eq("url", recipe["url"]).execute()
    if existing.data:
        return False

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

    supabase.table("Recipes").insert(row).execute()
    return True


def log_search(supabase: Client, query: str, sites: Optional[List[str]], results: int):
    supabase.table("search_log").insert({
        "query":          query,
        "sites_used":     ','.join(sites) if sites else 'all',
        "results_found":  results,
        "searched_at":    datetime.now().isoformat(),
    }).execute()


def list_recipes(supabase: Client, limit: int = 50):
    # FIX 1: consistent lowercase table name
    rows = supabase.table("Recipes") \
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
    total = supabase.table("Recipes").select("id", count="exact").execute().count
    print(f"\n  Showing {len(rows)} of {total} saved recipe(s).")


def view_recipe(supabase: Client, recipe_id: int):
    # FIX 1: consistent lowercase table name
    rows = supabase.table("Recipes").select("*").eq("id", recipe_id).execute().data
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
        urls: List[str] = load_recipe_sites()
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
        target_sites = sites if sites is not None else DEFAULT_RECIPE_SITES
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
                'instructions': self._clean_instructions(scraper),
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

    def _clean_instructions(self, scraper) -> str:
        """
        FIX 2: Try to get instructions as a list first (preserves step boundaries),
        then fall back to the raw string. Normalizes all newline variants to ' | '
        so the API can reliably split on it.
        """
        # Try list form first — recipe-scrapers exposes instructions_list() on many scrapers
        steps: List[str] = []
        try:
            steps = scraper.instructions_list()
        except Exception:
            pass

        if steps:
            cleaned_steps = [re.sub(r'\s+', ' ', s).strip() for s in steps if s.strip()]
            joined = ' | '.join(cleaned_steps)
        else:
            # Fall back to raw string and split on newlines
            try:
                raw = scraper.instructions() or ''
            except Exception:
                return ''
            # Normalize any run of newlines/whitespace-only lines into our separator
            joined = re.sub(r'\n+', ' | ', raw.strip())
            joined = re.sub(r'\s+', ' ', joined).strip()
            # Collapse accidental double separators
            joined = re.sub(r'(\s*\|\s*){2,}', ' | ', joined)

        return joined[:2000] + '...' if len(joined) > 2000 else joined

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

            # Vegan / Vegetarian
            text = ' '.join(ingredients).lower()
            if self._is_vegan(ingredients):
                tags.append('vegan')
            elif self._is_vegetarian(ingredients):
                tags.append('vegetarian')
            
            # Pescatarian
            if self._is_pescatarian(ingredients):
                tags.append('pescatarian')
            
            # Gluten-Free
            GLUTEN_SOURCES = {
                'flour', 'wheat', 'barley', 'rye', 'spelt', 'farro', 'bulgur',
                'semolina', 'durum', 'triticale', 'malt', 'bread', 'breadcrumbs',
                'pasta', 'noodles', 'couscous', 'cracker', 'tortilla', 'pita',
                'soy sauce', 'teriyaki', 'panko', 'seitan', 'beer',
            }
            GLUTEN_FREE_SIGNALS = {'gluten-free', 'gluten free', 'gf flour', 'rice flour',
                                   'almond flour', 'coconut flour', 'tapioca flour'}
            has_gf_signal  = any(s in text for s in GLUTEN_FREE_SIGNALS)
            has_gluten     = any(re.search(rf'\b{re.escape(g)}\b', text) for g in GLUTEN_SOURCES)
            if has_gf_signal or not has_gluten:
                tags.append('gluten-free')
            
            # Lactose-Free
            DAIRY_SOURCES = {
                'milk', 'cheese', 'butter', 'cream', 'yogurt', 'yoghurt',
                'whey', 'casein', 'lactose', 'ghee', 'kefir', 'sour cream',
                'half-and-half', 'half and half', 'ice cream', 'custard',
                'bechamel', 'béchamel',
            }
            DAIRY_FREE_SIGNALS = {'dairy-free', 'dairy free', 'non-dairy', 'nondairy',
                                   'lactose-free', 'lactose free', 'plant-based milk',
                                   'almond milk', 'oat milk', 'soy milk', 'coconut milk',
                                   'vegan butter', 'vegan cheese'}
            has_df_signal = any(s in text for s in DAIRY_FREE_SIGNALS)
            has_dairy     = any(re.search(rf'\b{re.escape(d)}\b', text) for d in DAIRY_SOURCES)
            if has_df_signal or not has_dairy:
                tags.append('lactose-free')
            
            # Nut Allergy / Nut-Free
            NUT_SOURCES = {
                'almond', 'almonds', 'cashew', 'cashews', 'walnut', 'walnuts',
                'pecan', 'pecans', 'pistachio', 'pistachios', 'hazelnut', 'hazelnuts',
                'macadamia', 'pine nut', 'pine nuts', 'brazil nut', 'brazil nuts',
                'peanut', 'peanuts', 'peanut butter', 'nut butter', 'almond butter',
                'almond flour', 'almond milk', 'marzipan', 'praline', 'nutella',
                'mixed nuts', 'chopped nuts',
            }
            has_nuts = any(re.search(rf'\b{re.escape(n)}\b', text) for n in NUT_SOURCES)
            if not has_nuts:
                tags.append('nut-free')
            
            # Shellfish Allergy / Shellfish-Free
            SHELLFISH_SOURCES = {
                'shrimp', 'prawn', 'prawns', 'crab', 'lobster', 'crayfish',
                'crawfish', 'scallop', 'scallops', 'clam', 'clams', 'oyster',
                'oysters', 'mussel', 'mussels', 'barnacle', 'krill',
                'cuttlefish', 'squid', 'calamari', 'octopus',
                'seafood sauce', 'shrimp paste', 'fish sauce',
            }
            has_shellfish = any(re.search(rf'\b{re.escape(s)}\b', text) for s in SHELLFISH_SOURCES)
            if not has_shellfish:
                tags.append('shellfish-free')

            # Diabetic-Friendly (flags high-sugar / high-carb) -- not perfect
            HIGH_SUGAR_CARB = {
                'sugar', 'brown sugar', 'powdered sugar', 'caster sugar',
                'corn syrup', 'high fructose', 'honey', 'maple syrup', 'agave',
                'molasses', 'jam', 'jelly', 'condensed milk', 'caramel',
                'frosting', 'icing', 'candy', 'chocolate chips',
                'white rice', 'white bread', 'white flour', 'pasta',
                'potato', 'potatoes', 'sweet potato',
            }
            LOW_SUGAR_SIGNALS = {'sugar-free', 'sugar free', 'no sugar', 'zero sugar',
                                 'diabetic', 'low-carb', 'low carb', 'no added sugar'}
            has_ls_signal   = any(s in text for s in LOW_SUGAR_SIGNALS)
            has_high_sc     = any(re.search(rf'\b{re.escape(h)}\b', text) for h in HIGH_SUGAR_CARB)
            # Try nutrition data first
            try:
                nutrients = scraper.nutrients() or {}
                sugar_str = nutrients.get('sugarContent', '')
                carb_str  = nutrients.get('carbohydrateContent', '')
                sugar_g   = float(re.search(r'[\d.]+', sugar_str).group()) if sugar_str else None
                carb_g    = float(re.search(r'[\d.]+', carb_str).group()) if carb_str else None
                if (sugar_g is not None and carb_g is not None
                        and sugar_g <= 10 and carb_g <= 30):
                    tags.append('diabetic-friendly')
                elif has_ls_signal and not has_high_sc:
                    tags.append('diabetic-friendly')
            except Exception:
                if has_ls_signal or not has_high_sc:
                    tags.append('diabetic-friendly')
            
            # Keto
            KETO_DISQUALIFIERS = {
                'sugar', 'honey', 'maple syrup', 'corn syrup', 'agave',
                'white flour', 'wheat flour', 'bread', 'pasta', 'rice',
                'potato', 'oat', 'oats', 'oatmeal', 'beans', 'lentils',
                'chickpeas', 'corn', 'tortilla', 'cracker', 'granola',
            }
            KETO_SIGNALS = {'keto', 'ketogenic', 'low-carb', 'low carb'}
            has_keto_signal = any(s in text for s in KETO_SIGNALS)
            has_keto_disq   = any(re.search(rf'\b{re.escape(k)}\b', text) for k in KETO_DISQUALIFIERS)
            try:
                nutrients = scraper.nutrients() or {}
                carb_str  = nutrients.get('carbohydrateContent', '')
                carb_g    = float(re.search(r'[\d.]+', carb_str).group()) if carb_str else None
                if carb_g is not None and carb_g <= 10:
                    tags.append('keto')
                elif has_keto_signal and not has_keto_disq:
                    tags.append('keto')
            except Exception:
                if has_keto_signal and not has_keto_disq:
                    tags.append('keto')

            # Low-Calorie
            HIGH_CAL_INGREDIENTS = {
                'butter', 'oil', 'cream', 'lard', 'shortening', 'sugar',
                'chocolate', 'cheese', 'bacon', 'mayonnaise', 'peanut butter',
                'coconut cream', 'heavy cream', 'full-fat',
            }
            LOW_CAL_SIGNALS = {'low-calorie', 'low calorie', 'light', 'diet', 'reduced-fat',
                                'reduced fat', 'low-fat', 'low fat', 'skinny', 'low-cal',
                                'low cal', 'lowcal', 'lowfat'}
            has_lc_signal = any(s in text for s in LOW_CAL_SIGNALS)
            try:
                nutrients   = scraper.nutrients() or {}
                cal_str     = nutrients.get('calories', '')
                cal_val     = float(re.search(r'[\d.]+', cal_str).group()) if cal_str else None
                if cal_val is not None and cal_val <= 400:
                    tags.append('low-calorie')
                elif has_lc_signal:
                    tags.append('low-calorie')
            except Exception:
                if has_lc_signal:
                    tags.append('low-calorie')

            # High-Protein
            HIGH_PROTEIN_INGREDIENTS = {
                'chicken', 'beef', 'pork', 'turkey', 'tuna', 'salmon', 'egg',
                'eggs', 'lentils', 'chickpeas', 'black beans', 'edamame',
                'tofu', 'tempeh', 'cottage cheese', 'greek yogurt',
                'protein powder', 'whey', 'quinoa',
            }
            HIGH_PROTEIN_SIGNALS = {'high-protein', 'high protein', 'protein-packed',
                                    'protein packed'}
            has_hp_signal = any(s in text for s in HIGH_PROTEIN_SIGNALS)
            has_protein_ing = any(re.search(rf'\b{re.escape(p)}\b', text)
                                  for p in HIGH_PROTEIN_INGREDIENTS)
            try:
                nutrients  = scraper.nutrients() or {}
                prot_str   = nutrients.get('proteinContent', '')
                prot_g     = float(re.search(r'[\d.]+', prot_str).group()) if prot_str else None
                if prot_g is not None and prot_g >= 20:
                    tags.append('high-protein')
                elif has_hp_signal or has_protein_ing:
                    tags.append('high-protein')
            except Exception:
                if has_hp_signal or has_protein_ing:
                    tags.append('high-protein')

            # Halal
            HARAM_INGREDIENTS = {
                'pork', 'bacon', 'ham', 'lard', 'prosciutto', 'pepperoni',
                'salami', 'sausage', 'chorizo', 'gelatin', 'beer', 'wine',
                'alcohol', 'liqueur', 'rum', 'vodka', 'whiskey', 'brandy',
                'sake', 'mirin', 'cooking wine',
            }
            HALAL_SIGNALS = {'halal'}
            has_halal_signal = any(s in text for s in HALAL_SIGNALS)
            has_haram = any(re.search(rf'\b{re.escape(h)}\b', text) for h in HARAM_INGREDIENTS)
            if has_halal_signal or not has_haram:
                tags.append('halal')
            
            # Kosher -- simplified
            TREIF_INGREDIENTS = {
                'pork', 'bacon', 'ham', 'lard', 'prosciutto', 'pepperoni',
                'salami', 'chorizo', 'shrimp', 'crab', 'lobster', 'clam',
                'oyster', 'mussel', 'scallop', 'squid', 'calamari', 'octopus',
                'rabbit', 'catfish', 'eel',
            }
            # Cannot mix meat and dairy
            MEAT_WORDS  = {'chicken', 'beef', 'lamb', 'turkey', 'meat', 'steak',
                           'veal', 'brisket', 'ground beef', 'ground turkey'}
            DAIRY_WORDS = {'milk', 'cheese', 'butter', 'cream', 'yogurt', 'yoghurt',
                           'whey', 'sour cream', 'half and half'}
            KOSHER_SIGNALS = {'kosher'}
            has_kosher_signal = any(s in text for s in KOSHER_SIGNALS)
            has_treif    = any(re.search(rf'\b{re.escape(t)}\b', text) for t in TREIF_INGREDIENTS)
            has_meat_and_dairy = (
                any(re.search(rf'\b{re.escape(m)}\b', text) for m in MEAT_WORDS) and
                any(re.search(rf'\b{re.escape(d)}\b', text) for d in DAIRY_WORDS)
            )
            if has_kosher_signal or (not has_treif and not has_meat_and_dairy):
                tags.append('kosher')

            # Hindu-Friendly
            BEEF_SOURCES = {
                'beef', 'steak', 'brisket', 'veal', 'ground beef', 'ribeye',
                'sirloin', 'chuck', 'short rib', 'oxtail', 'beef broth',
                'beef stock', 'beef bouillon', 'suet', 'lard',
            }
            HINDU_SIGNALS = {'hindu'}
            has_hindu_signal = any(s in text for s in HINDU_SIGNALS)
            has_beef = any(re.search(rf'\b{re.escape(b)}\b', text) for b in BEEF_SOURCES)
            if has_hindu_signal or not has_beef:
                tags.append('hindu-friendly')

            # Buddhist - typically no meat and sometimes no alliums
            ALLIUMS = {'garlic', 'onion', 'onions', 'leek', 'leeks', 'shallot',
                       'shallots', 'chive', 'chives', 'scallion', 'scallions',
                       'spring onion'}
            MEAT_SOURCES = {
                'chicken', 'beef', 'pork', 'lamb', 'turkey', 'duck', 'veal',
                'bacon', 'ham', 'sausage', 'fish', 'shrimp', 'crab', 'lobster',
            }
            BUDDHIST_SIGNALS = {'buddhist'}
            has_buddhist_signal = any(s in text for s in BUDDHIST_SIGNALS)
            has_meat_b  = any(re.search(rf'\b{re.escape(m)}\b', text) for m in MEAT_SOURCES)
            has_alliums = any(re.search(rf'\b{re.escape(a)}\b', text) for a in ALLIUMS)
            if has_buddhist_signal or (not has_meat_b and not has_alliums):
                tags.append('buddhist-friendly')

            # Low-Sodium
            HIGH_SODIUM_INGREDIENTS = {
                'soy sauce', 'salt', 'table salt', 'kosher salt', 'sea salt',
                'fish sauce', 'oyster sauce', 'worcestershire', 'anchovies',
                'capers', 'olives', 'pickles', 'miso', 'tamari',
                'canned tomatoes', 'canned beans', 'stock', 'broth', 'bouillon',
                'deli meat', 'bacon', 'ham', 'sausage', 'salami', 'pepperoni',
            }
            LOW_SODIUM_SIGNALS = {'low-sodium', 'low sodium', 'no salt', 'unsalted',
                                   'reduced sodium', 'sodium-free', 'sodium free'}
            has_lsod_signal = any(s in text for s in LOW_SODIUM_SIGNALS)
            has_high_sodium = any(re.search(rf'\b{re.escape(h)}\b', text)
                                  for h in HIGH_SODIUM_INGREDIENTS)
            try:
                nutrients = scraper.nutrients() or {}
                sod_str   = nutrients.get('sodiumContent', '')
                sod_mg    = float(re.search(r'[\d.]+', sod_str).group()) if sod_str else None
                if sod_mg is not None and sod_mg <= 600:
                    tags.append('low-sodium')
                elif has_lsod_signal or not has_high_sodium:
                    tags.append('low-sodium')
            except Exception:
                if has_lsod_signal or not has_high_sodium:
                    tags.append('low-sodium')
            
            # Paleo
            PALEO_DISQUALIFIERS = {
                'sugar', 'brown sugar', 'white sugar', 'cane sugar', 'powdered sugar',
                'caster sugar', 'corn syrup', 'high fructose', 'artificial sweetener',
                'splenda', 'aspartame', 'sucralose',
                # grains
                'wheat', 'flour', 'bread', 'pasta', 'rice', 'oat', 'oats', 'oatmeal',
                'barley', 'rye', 'corn', 'cornmeal', 'cornstarch', 'couscous',
                'quinoa', 'granola', 'cereal', 'cracker', 'tortilla', 'breadcrumbs',
                # legumes
                'beans', 'lentils', 'chickpeas', 'peanut', 'peanuts', 'peanut butter',
                'soy', 'tofu', 'tempeh', 'edamame', 'miso', 'soy sauce', 'tamari',
                # dairy
                'milk', 'cheese', 'butter', 'cream', 'yogurt', 'yoghurt',
                'whey', 'casein', 'ghee', 'kefir', 'sour cream', 'ice cream',
                # processed / industrial
                'canola oil', 'vegetable oil', 'soybean oil', 'corn oil',
                'margarine', 'shortening', 'msg', 'maltodextrin',
            }
            PALEO_SIGNALS = {'paleo', 'paleolithic', 'primal'}
            has_paleo_signal = any(s in text for s in PALEO_SIGNALS)
            has_paleo_disq   = any(
                re.search(rf'\b{re.escape(p)}\b', text) for p in PALEO_DISQUALIFIERS
            )
            if has_paleo_signal or not has_paleo_disq:
                tags.append('paleo')
        except Exception:
            pass
        return tags

    def _is_vegan(self, ingredients: List[str]) -> bool:
        NON_VEGAN = {
            # Meat
            'meat', 'chicken', 'beef', 'pork', 'ham', 'bacon', 'sausage',
            'turkey', 'lamb', 'duck', 'veal', 'goat', 'rabbit', 'venison',
            'salami', 'pepperoni', 'prosciutto',
            # Seafood
            'fish', 'anchovy', 'anchovies', 'shrimp', 'prawn', 'prawns',
            'crab', 'lobster', 'shellfish', 'salmon', 'tuna', 'cod',
            'sardine', 'sardines', 'mussel', 'mussels', 'clam', 'clams',
            'oyster', 'oysters', 'scallop', 'scallops', 'squid', 'octopus',
            # Dairy
            'milk', 'cheese', 'butter', 'cream', 'ghee', 'whey', 'casein',
            'lactose', 'lactalbumin', 'kefir', 'buttermilk', 'custard',
            'yogurt', 'yoghurt',
            # Eggs
            'egg', 'eggs', 'albumin', 'albumen', 'mayonnaise', 'meringue',
            # Animal-derived additives
            'honey', 'gelatin', 'lard', 'suet', 'tallow', 'rennet',
            'isinglass', 'carmine', 'cochineal', 'shellac', 'collagen',
            'lanolin',
        }
        text = ' '.join(ingredients).lower()
        return not any(re.search(rf'\b{re.escape(w)}\b', text) for w in NON_VEGAN)

    def _is_vegetarian(self, ingredients: List[str]) -> bool:
        NON_VEG = {
            # Meat
            'meat', 'chicken', 'beef', 'pork', 'ham', 'bacon', 'sausage',
            'turkey', 'lamb', 'duck', 'veal', 'goat', 'rabbit', 'venison',
            'bison', 'quail', 'goose', 'salami', 'pepperoni', 'prosciutto',
            # Seafood
            'fish', 'salmon', 'tuna', 'cod', 'tilapia', 'sardine', 'sardines',
            'herring', 'mackerel', 'anchovy', 'anchovies', 'shrimp', 'prawn',
            'prawns', 'crab', 'lobster', 'squid', 'octopus', 'scallop', 'scallops',
            'clam', 'clams', 'oyster', 'oysters', 'mussel', 'mussels',
            # Animal-derived
            'lard', 'suet', 'tallow', 'gelatin', 'rennet', 'isinglass',
            'carmine', 'cochineal', 'dashi',
        }
        text = ' '.join(ingredients).lower()
        return not any(re.search(rf'\b{re.escape(w)}\b', text) for w in NON_VEG)

    def _is_pescatarian(self, ingredients: List[str]) -> bool:
        LAND_MEAT = {
            'chicken', 'beef', 'pork', 'bacon', 'ham', 'sausage', 'lamb',
            'turkey', 'duck', 'veal', 'lard', 'suet', 'meat', 'gelatin',
            'chorizo', 'salami', 'pepperoni', 'prosciutto', 'brisket',
        }
        text = ' '.join(ingredients).lower()
        return not any(re.search(rf'\b{re.escape(m)}\b', text) for m in LAND_MEAT)

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
            sites = load_recipe_sites()
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
