// app/search/page.tsx
'use client'
import { useState } from 'react'

import Link from 'next/link'

interface RecipeSummary {
  id: number
  title: string
  source_site: string
  image_url: string
  total_time: string
  yields: string
  cuisine: string
  dietary_tags: string
  calories: string
}


const API_BASE = process.env.NEXT_PUBLIC_SUPABASE_URL
if (!API_BASE) {
  console.warn("NEXT_PUBLIC_SUPABASE_URL is not set — API calls will fail")
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL?? "http://localhost:8000"


export default function RecipesPage() {
  const [text, setText] = useState('')
  const [results, setResults] = useState<RecipeSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)


  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    if (!API_BASE) {
      setError("API URL is not configured. Please contact the site administrator.")
      return
    }
    setLoading(true)
    setSearched(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_BASE}/api/recipes?q=${encodeURIComponent(text)}&limit=20`
      )
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError("Something went wrong. Please try again.")
      setResults([])
    } finally {
      setLoading(false)
    }

const handleSearch = async (e: React.FormEvent) => {
  e.preventDefault()
  console.log("API_BASE:", API_BASE) 
  console.log("FULL URL:", `${API_BASE}/api/recipes?q=${text}`) 
  if (!text.trim()) return
  setLoading(true)
  setSearched(true)
  try {
    const res = await fetch(
      `${API_BASE}/api/recipes?q=${encodeURIComponent(text)}&limit=20`
    )
    const data = await res.json()
    setResults(data)
  } catch {
    setResults([])
  } finally {
    setLoading(false)

  }
}

  return (
    <div className="page-content fade-up">

      {/* HEADING */}
      <span className="section-label">Discover</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 8 }}>
        Recipe Search
      </h1>
      <p style={{ marginBottom: 40, fontSize: "0.95rem", maxWidth: 500 }}>
        Search by ingredients, cuisine type, dietary preferences, and ratings!
      </p>

      {/* SEARCH BAR */}
      <form onSubmit={handleSearch} style={{ display: "flex", gap: 0, maxWidth: 560, marginBottom: 48 }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. 3 Onions, Vegetarian, Gluten-Free"
          aria-label="Search recipes"
          style={{ flex: 1, borderRadius: "4px 0 0 4px", borderRight: "none" }}
        />
        <button
          type="submit"
          className="btn"
          style={{ borderRadius: "0 4px 4px 0", whiteSpace: "nowrap" }}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <hr className="divider" style={{ marginBottom: 48 }} />

      {/* RESULTS */}
      <span className="section-label" style={{ marginBottom: 20, display: "block" }}>Results</span>

      {!searched && (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          Searched recipes will appear here
        </p>
      )}

      {error && (
        <p style={{ color: "red", fontSize: "0.95rem", marginBottom: 16 }}>
          {error}
        </p>
      )}

      {loading && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card" style={{ opacity: 0.4, animation: "pulse 1.5s infinite" }}>
              <div style={{ height: 140, borderRadius: 4, background: "var(--border)", marginBottom: 12 }} />
              <div style={{ height: 12, borderRadius: 4, background: "var(--border)", marginBottom: 8 }} />
              <div style={{ height: 8, borderRadius: 4, background: "var(--border)", width: "70%", marginBottom: 8 }} />
              <div style={{ height: 8, borderRadius: 4, background: "var(--border)", width: "50%" }} />
            </div>
          ))}
        </div>
      )}

      {searched && !loading && !error && results.length === 0 && (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          No recipes found for <strong>"{text}"</strong>. Try different keywords.
        </p>
      )}

      {!loading && results.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
          {results.map((r) => (
            <Link
              key={r.id}
              href={`/recipes/${r.id}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit", display: "block" }}
            >
              {r.image_url && (
                <img
                  src={r.image_url}
                  alt={r.title}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  style={{ width: "100%", height: 140, objectFit: "cover", borderRadius: 4, marginBottom: 12 }}
                />
              )}
              <p style={{ fontWeight: 600, marginBottom: 4, fontSize: "0.95rem" }}>{r.title}</p>
              <p style={{ fontSize: "0.78rem", color: "var(--ink-muted)", marginBottom: 4 }}>
                {r.source_site}{r.total_time ? ` · ${r.total_time}` : ""}{r.cuisine ? ` · ${r.cuisine}` : ""}
              </p>
              {r.dietary_tags && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {r.dietary_tags.split(",").map((tag) => (
                    <span key={tag} className="pill" style={{ fontSize: "0.7rem" }}>
                      {tag.trim()}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}

    </div>
  )
}
