# backend/main.py
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from scraper_v2 import RecipeSearchScraper, list_recipes

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://drdancookbook.vercel.app")

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
    query = db.table("Recipes") \
        .select("id, title, source_site, image_url, total_time, yields, cuisine, dietary_tags, calories")
    
    if q:
        query = query.ilike("title", f"%{q}%")  # filter BEFORE limit
    
    query = query.order("id", desc=True).limit(limit)
    
    rows = query.execute().data
    return rows


# --- GET /api/recipes/:id ---
@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    db = get_db()
    rows = db.table("Recipes").select("*").eq("id", recipe_id).execute().data
    if not rows:
        return {"error": "Not found"}
    r = rows[0]
    r["ingredients"] = (r["ingredients"] or "").split(" | ")
    r["instructions"] = (r["instructions"] or "").split(" | ")
    return r


# --- POST /api/scrape  body: { "query": "pasta", "num_results": 10 } ---
def run_scrape(query: str, num_results: int):
    scraper = RecipeSearchScraper()
    scraper.search_and_scrape(query=query, num_results=num_results)

@app.post("/api/scrape")
def trigger_scrape(body: dict, background_tasks: BackgroundTasks):
    query = body.get("query", "")
    num_results = body.get("num_results", 10)
    if not query:
        return {"error": "query required"}
    background_tasks.add_task(run_scrape, query, num_results)
    return {"status": "scraping started", "query": query}
