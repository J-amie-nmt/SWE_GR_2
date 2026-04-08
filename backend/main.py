# backend/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from scraper_v2 import RecipeSearchScraper

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://drdancookbook.vercel.app")
SCRAPE_SECRET = os.environ.get("SCRAPE_SECRET", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# --- GET /api/recipes?q=pasta&limit=20 ---
@app.get("/api/recipes")
def search_recipes(q: str = "", limit: int = 20):
    db = get_db()
    # FIX 1: Table name is lowercase "recipes" everywhere — match your Supabase table name
    query = db.table("Recipes") \
        .select("id, title, source_site, image_url, total_time, yields, cuisine, dietary_tags, calories")

    if q:
        # FIX 2: Search across title, dietary_tags, cuisine, and ingredients — not just title
        query = query.or_(
            f"title.ilike.%{q}%,"
            f"dietary_tags.ilike.%{q}%,"
            f"cuisine.ilike.%{q}%,"
            f"ingredients.ilike.%{q}%"
        )

    query = query.order("id", desc=True).limit(limit)
    rows = query.execute().data
    return rows


# --- GET /api/recipes/:id ---
@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    db = get_db()
    # FIX 1: consistent lowercase table name
    rows = db.table("Recipes").select("*").eq("id", recipe_id).execute().data

    # FIX 3: raise a proper 404 so the frontend error state triggers correctly
    if not rows:
        raise HTTPException(status_code=404, detail="Recipe not found")

    r = rows[0]
    # Safely split pipe-delimited strings into arrays, filtering empty strings
    r["ingredients"] = [i for i in (r.get("ingredients") or "").split(" | ") if i.strip()]
    r["instructions"] = [i for i in (r.get("instructions") or "").split(" | ") if i.strip()]
    return r


# --- POST /api/scrape  body: { "query": "pasta", "num_results": 10 } ---
def run_scrape(query: str, num_results: int):
    scraper = RecipeSearchScraper()
    scraper.search_and_scrape(query=query, num_results=num_results)


@app.post("/api/scrape")
def trigger_scrape(
    body: dict,
    background_tasks: BackgroundTasks,
    x_scrape_secret: str = Header(None),  # FIX 4: protect scrape endpoint
):
    if not SCRAPE_SECRET or x_scrape_secret != SCRAPE_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = body.get("query", "")
    num_results = body.get("num_results", 10)
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    background_tasks.add_task(run_scrape, query, num_results)
    return {"status": "scraping started", "query": query}
