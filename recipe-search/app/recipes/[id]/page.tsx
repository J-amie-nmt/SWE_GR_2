// app/recipes/[id]/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

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

export default function RecipeDetailPage() {
  const { id } = useParams()
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch(`http://localhost:8000/api/recipes/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error()
        return res.json()
      })
      .then((data) => {
        setRecipe(data)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [id])

  if (loading) return (
    <div className="page-content fade-up">
      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 700 }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ height: i === 1 ? 320 : 16, borderRadius: 4, background: "var(--border)", opacity: 0.4 }} />
        ))}
      </div>
    </div>
  )

  if (error || !recipe) return (
    <div className="page-content fade-up">
      <p style={{ color: "var(--ink-muted)" }}>Recipe not found.</p>
      <Link href="/recipes" className="btn" style={{ marginTop: 16, display: "inline-block" }}>Back to Search</Link>
    </div>
  )

  const nutrients = [
    { label: "Calories",      value: recipe.calories },
    { label: "Fat",           value: recipe.fat_content },
    { label: "Carbs",         value: recipe.carbohydrate_content },
    { label: "Protein",       value: recipe.protein_content },
    { label: "Sodium",        value: recipe.sodium_content },
  ].filter((n) => n.value)

  return (
    <div className="page-content fade-up" style={{ maxWidth: 740 }}>

      {/* BACK */}
      <Link href="/recipes" style={{ fontSize: "0.85rem", color: "var(--ink-muted)", textDecoration: "none", display: "inline-block", marginBottom: 24 }}>
        ← Back to Search
      </Link>

      {/* IMAGE */}
      {recipe.image_url && (
        <img
          src={recipe.image_url}
          alt={recipe.title}
          style={{ width: "100%", maxHeight: 340, objectFit: "cover", borderRadius: 8, marginBottom: 28 }}
        />
      )}

      {/* TITLE */}
      <span className="section-label">{recipe.source_site}</span>
      <h1 style={{ fontFamily: "'Fraunces', serif", fontSize: "clamp(1.6rem, 4vw, 2.4rem)", marginTop: 8, marginBottom: 12 }}>
        {recipe.title}
      </h1>

      {/* META PILLS */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
        {recipe.total_time  && <span className="pill">{recipe.total_time}</span>}
        {recipe.yields      && <span className="pill">{recipe.yields}</span>}
        {recipe.cuisine     && <span className="pill">{recipe.cuisine}</span>}
        {recipe.dietary_tags && recipe.dietary_tags.split(',').map((t) => (
          <span key={t} className="pill">{t.trim()}</span>
        ))}
      </div>

      <hr className="divider" style={{ marginBottom: 36 }} />

      {/* NUTRITION */}
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

      {/* INGREDIENTS */}
      <span className="section-label" style={{ marginBottom: 12, display: "block" }}>Ingredients</span>
      <ul style={{ paddingLeft: 20, marginBottom: 36 }}>
        {recipe.ingredients.map((ing, i) => (
          <li key={i} style={{ marginBottom: 6, fontSize: "0.93rem" }}>{ing}</li>
        ))}
      </ul>

      <hr className="divider" style={{ marginBottom: 36 }} />

      {/* INSTRUCTIONS */}
      <span className="section-label" style={{ marginBottom: 12, display: "block" }}>Instructions</span>
      <ol style={{ paddingLeft: 20, marginBottom: 36 }}>
        {recipe.instructions.map((step, i) => (
          <li key={i} style={{ marginBottom: 12, fontSize: "0.93rem", lineHeight: 1.6 }}>{step}</li>
        ))}
      </ol>

      {/* SOURCE LINK */}
      <a href={recipe.url} target="_blank" rel="noopener noreferrer" className="btn">
        View Original Recipe ↗
      </a>

    </div>
  )
}
