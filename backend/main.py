from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os, re
from datetime import datetime, timedelta, timezone
from scraper_v2 import RecipeSearchScraper
from pydantic import BaseModel
from typing import Literal

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


def sanitize(value: str) -> str:
    return re.sub(r"[%_\\]", "", value.strip())[:100]


@app.get("/api/recipes")
def search_recipes(
    q: str = "",
    cuisine: str = "",
    diet: str = "",
    max_time: int | None = None,
    sort: Literal["newest", "title", "time"] = "newest",
    limit: int = Query(default=21, le=100),
    offset: int = Query(default=0, ge=0),
):
    db = get_db()

    query = db.table("Recipes").select(
        "id, title, source_site, image_url, total_time, yields, cuisine, dietary_tags, calories",
        count="exact"
    )

    if q:
        safe_q = sanitize(q)
        query = query.or_(
            f"title.ilike.%{safe_q}%,"
            f"ingredients.ilike.%{safe_q}%,"
            f"dietary_tags.ilike.%{safe_q}%,"
            f"cuisine.ilike.%{safe_q}%"
        )

    if cuisine:
        query = query.ilike("cuisine", f"%{sanitize(cuisine)}%")

    if diet:
        query = query.ilike("dietary_tags", f"%{sanitize(diet)}%")

    if max_time is not None:
        query = query.lte("total_time_minutes", max_time)

    if sort == "title":
        query = query.order("title", desc=False)
    elif sort == "time":
        query = query.order("total_time_minutes", desc=False, nullsfirst=False)
    else:
        query = query.order("id", desc=True)

    query = query.range(offset, offset + limit - 1)
    res = query.execute()

    return {
        "results": res.data,
        "total": res.count or 0,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/recipes/filters")
def get_filter_options():
    db = get_db()
    rows = db.table("Recipes").select("cuisine, dietary_tags").execute().data

    cuisines: set[str] = set()
    diets: set[str] = set()

    for r in rows:
        if r.get("cuisine"):
            cuisines.add(r["cuisine"].strip())
        if r.get("dietary_tags"):
            for tag in r["dietary_tags"].split(","):
                tag = tag.strip()
                if tag:
                    diets.add(tag)

    return {
        "cuisines": sorted(cuisines),
        "diets": sorted(diets),
    }


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


@app.get("/api/saved")
def get_saved_recipes(email: str):
    db = get_db()
    rows = db.table("saved_recipes").select("*").eq("user_email", email).order("saved_at", desc=True).execute().data
    return rows


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


@app.delete("/api/saved")
def unsave_recipe_for_user(body: SaveRecipeBody):
    db = get_db()
    db.table("saved_recipes").delete().eq("user_email", body.user_email).eq("recipe_id", body.recipe_id).execute()
    return {"status": "removed"}


class ScrapeRequestBody(BaseModel):
    query: str
    submitted_by: str


@app.get("/api/scrape-requests")
def get_scrape_requests(email: str):
    db = get_db()
    rows = db.table("scrape_requests") \
        .select("*") \
        .eq("submitted_by", email) \
        .order("created_at", desc=True) \
        .execute().data
    return rows


@app.post("/api/scrape-requests")
def create_scrape_request(body: ScrapeRequestBody):
    db = get_db()

    total = db.table("scrape_requests") \
        .select("id", count="exact") \
        .execute().count or 0

    if total >= 50:
        raise HTTPException(
            status_code=429,
            detail="The request queue is full right now. Check back soon!"
        )

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = db.table("scrape_requests") \
        .select("id", count="exact") \
        .eq("submitted_by", body.submitted_by) \
        .gte("created_at", week_ago) \
        .execute().count or 0

    if recent >= 3:
        raise HTTPException(
            status_code=429,
            detail="You've reached the 3 requests per week limit. Try again next week!"
        )

    db.table("scrape_requests").insert({
        "query": body.query.strip()[:200],
        "submitted_by": body.submitted_by,
        "status": "pending",
    }).execute()

    return {"status": "queued"}


def run_scrape(query: str, num_results: int):
    scraper = RecipeSearchScraper()
    scraper.search_and_scrape(query=query, num_results=num_results)


@app.post("/api/scrape")
def trigger_scrape(body: dict, background_tasks: BackgroundTasks, x_scrape_secret: str = Header(None)):
    if not SCRAPE_SECRET or x_scrape_secret != SCRAPE_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = body.get("query", "")
    num_results = body.get("num_results", 10)
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    background_tasks.add_task(run_scrape, query, num_results)
    return {"status": "scraping started", "query": query}
