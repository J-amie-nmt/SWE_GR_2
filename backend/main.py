# backend/main.py
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from scraper_v2 import RecipeSearchScraper, list_recipes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "scraper", "recipes_V2.db")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- GET /api/recipes?q=pasta&limit=20 ---
@app.get("/api/recipes")
def search_recipes(q: str = "", limit: int = 20):
    db = get_db()
    rows = db.execute(
        "SELECT id, title, source_site, image_url, total_time, "
        "yields, cuisine, dietary_tags, calories "
        "FROM recipes WHERE title LIKE ? ORDER BY id DESC LIMIT ?",
        (f"%{q}%", limit)
    ).fetchall()
    return [dict(r) for r in rows]

# --- GET /api/recipes/:id ---
@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,)).fetchone()
    if not row:
        return {"error": "Not found"}, 404
    r = dict(row)
    r["ingredients"] = (r["ingredients"] or "").split(" | ")
    r["instructions"] = (r["instructions"] or "").split(" | ")
    return r

# --- POST /api/scrape  body: { "query": "pasta", "num_results": 10 } ---
def run_scrape(query: str, num_results: int):
    scraper = RecipeSearchScraper(DB_PATH)
    scraper.search_and_scrape(query=query, num_results=num_results)

@app.post("/api/scrape")
def trigger_scrape(body: dict, background_tasks: BackgroundTasks):
    query = body.get("query", "")
    num_results = body.get("num_results", 10)
    if not query:
        return {"error": "query required"}
    background_tasks.add_task(run_scrape, query, num_results)
    return {"status": "scraping started", "query": query}