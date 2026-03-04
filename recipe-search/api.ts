// recipe-search/src/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface RecipeSummary {
  id: number;
  title: string;
  source_site: string;
  image_url: string;
  total_time: string;
  yields: string;
  cuisine: string;
  dietary_tags: string;
  calories: string;
}

export interface RecipeDetail extends RecipeSummary {
  author: string;
  url: string;
  category: string;
  ingredients: string[];
  instructions: string[];
  fat_content: string;
  carbohydrate_content: string;
  protein_content: string;
}

export async function searchRecipes(q: string, limit = 20): Promise<RecipeSummary[]> {
  const res = await fetch(`${BASE}/api/recipes?q=${encodeURIComponent(q)}&limit=${limit}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getRecipe(id: number): Promise<RecipeDetail> {
  const res = await fetch(`${BASE}/api/recipes/${id}`);
  if (!res.ok) throw new Error("Recipe not found");
  return res.json();
}

export async function triggerScrape(query: string, num_results = 10) {
  const res = await fetch(`${BASE}/api/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, num_results }),
  });
  return res.json();
}