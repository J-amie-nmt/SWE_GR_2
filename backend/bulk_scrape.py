"""
bulk_scrape.py
==============
Runs scraper_v2.py sequentially across a large wordlist of recipe search terms.
Skips queries already logged in the `search_log` Supabase table.

Usage:
    python bulk_scrape.py                         # Run with defaults
    python bulk_scrape.py --delay 2.0             # 2s between requests
    python bulk_scrape.py --num-results 35        # 15 recipes per query
    python bulk_scrape.py --dry-run               # Preview terms only
    python bulk_scrape.py --resume                # Skip already-logged queries (default ON)
    python bulk_scrape.py --category proteins     # Run only one category

Dependencies: same as scraper_v2.py (must be in same directory)
"""

import argparse
import time
from datetime import datetime
from supabase import create_client
import os

# ── import your existing scraper ────────────────────────────────────────────
from scraper_v3_railway import RecipeSearchScraper, log_search

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


# ════════════════════════════════════════════════════════════════════════════
#  WORDLIST  — add / remove terms freely
# ════════════════════════════════════════════════════════════════════════════

RECIPE_TERMS: dict[str, list[str]] = {

    "proteins": [
        "chicken breast", "chicken thighs", "rotisserie chicken", "chicken soup",
        "ground beef", "beef stew", "beef stir fry", "pot roast", "meatballs",
        "pork chops", "pulled pork", "pork tenderloin", "bacon",
        "salmon", "shrimp", "tilapia", "tuna", "cod", "halibut", "scallops",
        "lamb chops", "rack of lamb",
        "turkey breast", "turkey meatloaf",
        "tofu", "tempeh", "lentils", "chickpeas", "black beans", "edamame",
        "eggs scrambled", "frittata", "quiche",
    ],

    "pasta_grains": [
        "spaghetti carbonara", "fettuccine alfredo", "pasta primavera",
        "lasagna", "baked ziti", "mac and cheese", "pasta bolognese",
        "cacio e pepe", "pesto pasta", "orzo salad",
        "fried rice", "risotto", "pilaf", "quinoa salad", "couscous",
        "ramen", "udon", "pad thai", "lo mein", "soba noodles",
        "gnocchi", "pierogi",
    ],

    "soups_stews": [
        "chicken noodle soup", "tomato soup", "french onion soup",
        "minestrone", "lentil soup", "split pea soup", "clam chowder",
        "beef chili", "white bean chili", "vegetable chili",
        "beef bourguignon", "chicken cacciatore", "coq au vin",
        "pho", "ramen broth", "miso soup", "hot and sour soup",
        "gumbo", "jambalaya", "bisque",
    ],

    "salads": [
        "caesar salad", "greek salad", "caprese salad", "nicoise salad",
        "cobb salad", "waldorf salad", "pasta salad", "potato salad",
        "taco salad", "kale salad", "arugula salad",
        "cucumber salad", "corn salad", "beet salad", "coleslaw",
        "quinoa salad", "chickpea salad",
    ],

    "vegetables_sides": [
        "roasted broccoli", "roasted cauliflower", "roasted asparagus",
        "roasted brussels sprouts", "roasted sweet potato", "roasted carrots",
        "mashed potatoes", "scalloped potatoes", "twice baked potatoes",
        "sauteed spinach", "creamed spinach", "stuffed peppers",
        "ratatouille", "eggplant parmesan", "zucchini fritters",
        "corn on the cob", "succotash", "glazed carrots",
    ],

    "breakfast": [
        "pancakes", "waffles", "french toast", "crepes",
        "breakfast burrito", "shakshuka", "eggs benedict",
        "granola", "overnight oats", "smoothie bowl",
        "banana bread", "blueberry muffins", "cinnamon rolls",
        "breakfast casserole", "hash browns", "avocado toast",
    ],

    "baking_bread": [
        "sourdough bread", "banana bread", "focaccia", "dinner rolls",
        "brioche", "pizza dough", "naan", "pita bread",
        "cornbread", "whole wheat bread", "bagels", "pretzels",
    ],

    "desserts": [
        "chocolate chip cookies", "brownies", "chocolate cake",
        "carrot cake", "cheesecake", "tiramisu", "creme brulee",
        "apple pie", "peach cobbler", "lemon bars", "panna cotta",
        "macarons", "eclairs", "profiteroles", "churros",
        "ice cream no churn", "mousse au chocolat", "sticky toffee pudding",
        "tres leches", "baklava",
    ],

    "cuisines_world": [
        "butter chicken", "chicken tikka masala", "dal makhani", "palak paneer",
        "beef tacos", "enchiladas", "chile verde", "tamales",
        "kung pao chicken", "mapo tofu", "orange chicken", "dumplings",
        "bibimbap", "japchae", "bulgogi",
        "falafel", "hummus", "shawarma", "tabbouleh",
        "moussaka", "spanakopita", "tzatziki",
        "jollof rice", "egusi soup",
    ],

    "sauces_condiments": [
        "marinara sauce", "bechamel sauce", "hollandaise", "chimichurri",
        "pesto", "romesco", "salsa verde", "tzatziki",
        "teriyaki sauce", "hoisin sauce", "tahini sauce",
        "ranch dressing", "caesar dressing", "vinaigrette",
    ],

    "dietary": [
        "vegan meal prep", "gluten free dinner", "keto chicken",
        "dairy free dessert", "paleo breakfast", "whole30 recipes",
        "low carb dinner", "high protein meal prep",
        "plant based protein", "nut free snacks",
    ],

    "seasonal": [
        "pumpkin soup", "butternut squash soup", "apple cider chicken",
        "cranberry sauce", "stuffing", "sweet potato casserole",
        "strawberry shortcake", "peach salsa", "corn chowder",
        "spring pea risotto", "asparagus tart",
    ],

    "quick_easy": [
        "15 minute dinner", "one pot pasta", "sheet pan chicken",
        "instant pot beef", "air fryer chicken wings", "air fryer salmon",
        "slow cooker chili", "slow cooker pot roast",
        "5 ingredient dinner", "meal prep bowls",
    ],
}

# Flat list in insertion order, deduped
ALL_TERMS: list[str] = list(dict.fromkeys(
    term for terms in RECIPE_TERMS.values() for term in terms
))


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def get_already_searched(supabase) -> set[str]:
    """Pull every query string already stored in search_log."""
    try:
        rows = supabase.table("search_log").select("query").execute().data
        return {r["query"].lower().strip() for r in rows}
    except Exception as e:
        print(f" Could not read search_log ({e}) — proceeding without skip list.")
        return set()


def print_progress(current: int, total: int, query: str, saved: int, elapsed: float):
    pct = (current / total) * 100
    eta_s = (elapsed / current) * (total - current) if current else 0
    eta = f"{int(eta_s // 60)}m {int(eta_s % 60)}s"
    print(
        f"\n{'─'*60}\n"
        f"  [{current}/{total}]  {pct:.0f}%   ETA ≈ {eta}\n"
        f"  Query   : '{query}'\n"
        f"  Saved   : {saved} new recipe(s)\n"
        f"{'─'*60}"
    )


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Bulk recipe scraper")
    parser.add_argument("--num-results",  type=int,   default=35,
                        help="Max recipes to scrape per query (default: 35)")
    parser.add_argument("--delay",        type=float, default=1.5,
                        help="Seconds between HTTP requests (default: 1.5)")
    parser.add_argument("--query-pause",  type=float, default=3.0,
                        help="Extra pause between queries in seconds (default: 3.0)")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Print terms only, do not scrape")
    parser.add_argument("--no-resume",    action="store_true",
                        help="Ignore search_log and re-run all terms")
    parser.add_argument("--category",     type=str,   default=None,
                        help="Run only one category (e.g. proteins, desserts)")
    args = parser.parse_args()

    # ── term list ────────────────────────────────────────────────────────────
    if args.category:
        cat = args.category.lower()
        if cat not in RECIPE_TERMS:
            print(f"Unknown category '{cat}'. Available: {', '.join(RECIPE_TERMS)}")
            return
        terms = RECIPE_TERMS[cat]
        print(f"Running category '{cat}' — {len(terms)} terms")
    else:
        terms = ALL_TERMS
        print(f"Running full wordlist — {len(terms)} terms across {len(RECIPE_TERMS)} categories")

    if args.dry_run:
        print("\n--- DRY RUN — terms that would be searched ---")
        for i, t in enumerate(terms, 1):
            print(f"  {i:>3}. {t}")
        return

    # ── supabase ─────────────────────────────────────────────────────────────
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY env vars.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    already_done: set[str] = set()
    if not args.no_resume:
        already_done = get_already_searched(supabase)
        skippable = sum(1 for t in terms if t.lower().strip() in already_done)
        print(f"  ✓ Resume mode ON — skipping {skippable} already-searched term(s)")

    pending = [t for t in terms if t.lower().strip() not in already_done]
    total   = len(pending)

    if total == 0:
        print("\nAll terms already searched! Use --no-resume to re-run them.")
        return

    print(f"\nStarting bulk scrape — {total} term(s) to process\n")

    scraper   = RecipeSearchScraper()
    grand_total_saved = 0
    start_time = time.time()

    for idx, query in enumerate(pending, 1):
        elapsed = time.time() - start_time

        saved = scraper.search_and_scrape(
            query=query,
            num_results=args.num_results,
            scrape_delay=args.delay,
        )
        grand_total_saved += saved
        print_progress(idx, total, query, saved, elapsed)

        # polite pause between queries
        if idx < total:
            print(f"Pausing {args.query_pause}s before next query…")
            time.sleep(args.query_pause)

    total_time = time.time() - start_time
    print(
        f"\n{'═'*60}\n"
        f"BULK SCRAPE COMPLETE\n"
        f"  Queries run : {total}\n"
        f"  Recipes saved : {grand_total_saved}\n"
        f"  Total time  : {int(total_time // 60)}m {int(total_time % 60)}s\n"
        f"{'═'*60}"
    )


if __name__ == "__main__":
    main()
