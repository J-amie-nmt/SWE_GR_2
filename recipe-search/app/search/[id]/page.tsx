// app/search/[id]/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useSession } from 'next-auth/react'

interface RecipeDetail {
  id: number
  title: string
  source_site: string
  image_url: string
  total_time: string
  yields: string
  cuisine: string
  category: string
  dietary_tags: string
  calories: string
  fat_content: string
  carbohydrate_content: string
  protein_content: string
  sodium_content: string
  author: string
  url: string
  ingredients: string[]
  instructions: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function RecipeDetailPage() {
  const params = useParams()
  const id = Array.isArray(params.id) ? params.id[0] : params.id

  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const { data: session } = useSession()
  const [saved, setSaved] = useState(false)
  const [saveLoading, setSaveLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    const controller = new AbortController()
    fetch(`${API_BASE}/api/recipes/${id}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        data.ingredients = Array.isArray(data.ingredients) ? data.ingredients : []
        data.instructions = Array.isArray(data.instructions) ? data.instructions : []
        setRecipe(data)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(true)
        setLoading(false)
      })
    return () => controller.abort()
  }, [id])

  useEffect(() => {
    if (!session?.user?.email || !recipe) return
    fetch(`${API_BASE}/api/saved?email=${encodeURIComponent(session.user.email)}`)
      .then(r => r.json())
      .then((list: { recipe_id: number }[]) => {
        setSaved(list.some(s => s.recipe_id === recipe.id))
      })
      .catch(() => {})
  }, [recipe, session])

  const handleSave = async () => {
    if (!session?.user?.email || !recipe) return
    setSaveLoading(true)
    const method = saved ? 'DELETE' : 'POST'
    try {
      await fetch(`${API_BASE}/api/saved`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email:   session.user.email,
          recipe_id:    recipe.id,
          title:        recipe.title,
          source_site:  recipe.source_site,
          image_url:    recipe.image_url,
          total_time:   recipe.total_time,
          cuisine:      recipe.cuisine,
          dietary_tags: recipe.dietary_tags,
        }),
      })
      setSaved(!saved)
    } catch {
      // optionally add a toast/error message here
    } finally {
      setSaveLoading(false)
    }
  }

  if (loading) return (
    <div className="page-content fade-up">
      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 700 }}>
        {[320, 20, 16, 16, 16].map((h, i) => (
          <div key={i} style={{ height: h, borderRadius: 4, background: "var(--border)", opacity: 0.4 }} />
        ))}
      </div>
    </div>
  )

  if (error || !recipe) return (
    <div className="page-content fade-up">
      <p style={{ color: "var(--ink-muted)" }}>Recipe not found.</p>
      <Link href="/search" className="btn" style={{ marginTop: 16, display: "inline-block" }}>
        Back to Search
      </Link>
    </div>
  )

  const nutrients = [
    { label: "Calories", value: recipe.calories },
    { label: "Fat", value: recipe.fat_content },
    { label: "Carbs", value: recipe.carbohydrate_content },
    { label: "Protein", value: recipe.protein_content },
    { label: "Sodium", value: recipe.sodium_content },
  ].filter((n) => n.value)

  return (
    <div className="page-content fade-up" style={{ maxWidth: 740 }}>

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <Link href="/search" style={{ fontSize: "0.85rem", color: "var(--ink-muted)", textDecoration: "none" }}>
          ← Back to Search
        </Link>

        {session && (
          <button
            onClick={handleSave}
            disabled={saveLoading}
            className="btn btn-outline"
            style={{ fontSize: "0.85rem", padding: "6px 14px" }}
          >
            {saveLoading ? "..." : saved ? "♥ Saved" : "♡ Save Recipe"}
          </button>
        )}
      </div>

      {recipe.image_url && (
        <img
          src={recipe.image_url}
          alt={recipe.title}
          style={{ width: "100%", maxHeight: 340, objectFit: "cover", borderRadius: 8, marginBottom: 28 }}
          onError={(e) => { e.currentTarget.style.display = 'none' }}
        />
      )}

      <span className="section-label">{recipe.source_site}</span>
      <h1 style={{ fontFamily: "'Fraunces', serif", fontSize: "clamp(1.6rem, 4vw, 2.4rem)", marginTop: 8, marginBottom: 12 }}>
        {recipe.title}
      </h1>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
        {recipe.total_time && <span className="pill">{recipe.total_time}</span>}
        {recipe.yields && <span className="pill">{recipe.yields}</span>}
        {recipe.cuisine && <span className="pill">{recipe.cuisine}</span>}
        {recipe.dietary_tags?.split(',').map((t) => (
          <span key={t} className="pill">{t.trim()}</span>
        ))}
      </div>

      <hr className="divider" style={{ marginBottom: 36 }} />

      {nutrients.length > 0 && (
        <>
          <span className="section-label" style={{ marginBottom: 12, display: "block" }}>Nutrition</span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 36 }}>
            {nutrients.map((n) => (
              <div key={n.label} className="card" style={{ padding: "12px 20px", minWidth: 100, textAlign: "center" }}>
                <span style={{ display: "block", fontFamily: "'Fraunces', serif", fontSize: "1.2rem", fontWeight: 700, color: "var(--accent)" }}>
                  {n.value}
                </span>
                <span style={{ fontSize: "0.72rem", color: "var(--ink-muted)" }}>{n.label}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <span className="section-label" style={{ marginBottom: 12, display: "block" }}>Ingredients</span>
      {recipe.ingredients.length > 0 ? (
        <ul style={{ paddingLeft: 20, marginBottom: 36 }}>
          {recipe.ingredients.map((ing, i) => (
            <li key={i} style={{ marginBottom: 6, fontSize: "0.93rem" }}>{ing}</li>
          ))}
        </ul>
      ) : (
        <p style={{ color: "var(--ink-muted)", marginBottom: 36 }}>No ingredients available.</p>
      )}

      <hr className="divider" style={{ marginBottom: 36 }} />

      <span className="section-label" style={{ marginBottom: 12, display: "block" }}>Instructions</span>
      {recipe.instructions.length > 0 ? (
        <ol style={{ paddingLeft: 20, marginBottom: 36 }}>
          {recipe.instructions.map((step, i) => (
            <li key={i} style={{ marginBottom: 12, fontSize: "0.93rem", lineHeight: 1.6 }}>{step}</li>
          ))}
        </ol>
      ) : (
        <p style={{ color: "var(--ink-muted)", marginBottom: 36 }}>No instructions available.</p>
      )}

      <a href={recipe.url} target="_blank" rel="noopener noreferrer" className="btn">
        View Original Recipe ↗
      </a>

    </div>
  )
}
