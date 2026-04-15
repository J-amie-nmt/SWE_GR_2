from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from scraper_v2 import RecipeSearchScraper
from pydantic import BaseModel

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


# --- GET /api/recipes?q=pasta&limit=20&offset=0 ---
@app.get("/api/recipes")
def search_recipes(q: str = "", limit: int = 20, offset: int = 0):
    db = get_db()

    query = db.table("Recipes").select(
        "id, title, source_site, image_url, total_time, yields, cuisine, dietary_tags, calories",
        count="exact"  # get total count
    )

    if q:
        query = query.or_(
            f"title.ilike.%{q}%,"
            f"dietary_tags.ilike.%{q}%,"
            f"cuisine.ilike.%{q}%,"
            f"ingredients.ilike.%{q}%"
        )

    query = query.order("id", desc=True) \
                 .range(offset, offset + limit - 1)

    res = query.execute()

    return {
        "results": res.data,
        "total": res.count or 0
    }


# --- GET /api/recipes/:id ---
@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    db = get_db()

    rows = db.table("Recipes").select("*").eq("id", recipe_id).execute().data

    if not rows:
        raise HTTPException(status_code=404, detail="Recipe not found")

    r = rows[0]

    r["ingredients"] = [i for i in (r.get("ingredients") or "").split(" | ") if i.strip()]
    r["instructions"] = [i for i in (r.get("instructions") or "").split(" | ") if i.strip()]

    return r


class SaveRecipeBody(BaseModel):
    user_email: str
    recipe_id: int
    title: str | None = None
    source_site: str | None = None
    image_url: str | None = None
    total_time: str | None = None
    cuisine: str | None = None
    dietary_tags: str | None = None


# --- GET /api/saved?email=user@email.com ---
@app.get("/api/saved")
def get_saved_recipes(email: str):
    db = get_db()

    rows = db.table("saved_recipes") \
        .select("*") \
        .eq("user_email", email) \
        .order("saved_at", desc=True) \
        .execute().data

    return rows


# --- POST /api/saved ---
@app.post("/api/saved")
def save_recipe_for_user(body: SaveRecipeBody):
    db = get_db()

    db.table("saved_recipes").upsert({
        "user_email":  body.user_email,
        "recipe_id":   body.recipe_id,
        "title":       body.title,
        "source_site": body.source_site,
        "image_url":   body.image_url,
        "total_time":  body.total_time,
        "cuisine":     body.cuisine,
        "dietary_tags": body.dietary_tags,
    }, on_conflict="user_email,recipe_id").execute()

    return {"status": "saved"}


# --- DELETE /api/saved ---
@app.delete("/api/saved")
def unsave_recipe_for_user(body: SaveRecipeBody):
    db = get_db()

    db.table("saved_recipes") \
        .delete() \
        .eq("user_email", body.user_email) \
        .eq("recipe_id", body.recipe_id) \
        .execute()

    return {"status": "removed"}


# --- Scraper ---
def run_scrape(query: str, num_results: int):
    scraper = RecipeSearchScraper()
    scraper.search_and_scrape(query=query, num_results=num_results)


# --- POST /api/scrape ---
@app.post("/api/scrape")
def trigger_scrape(
    body: dict,
    background_tasks: BackgroundTasks,
    x_scrape_secret: str = Header(None),
):
    if not SCRAPE_SECRET or x_scrape_secret != SCRAPE_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = body.get("query", "")
    num_results = body.get("num_results", 10)

    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    background_tasks.add_task(run_scrape, query, num_results)

    return {"status": "scraping started", "query": query}
