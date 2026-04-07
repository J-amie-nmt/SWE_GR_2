// app/search/page.tsx
'use client'
import { useState } from 'react'
import { createClient } from '@supabase/supabase-js'
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

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export default function RecipesPage() {
  const [text, setText] = useState('')
  const [results, setResults] = useState<RecipeSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

const handleSearch = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!text.trim()) return
  setLoading(true)
  setSearched(true)
  try {
    const { data } = await supabase
      .from('recipes')
      .select('id, title, source_site, image_url, total_time, yields, cuisine, dietary_tags, calories')
      .ilike('title', `%${text}%`)
      .order('id', { ascending: false })
      .limit(20)
    setResults(data || [])
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

      {searched && !loading && results.length === 0 && (
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
                  style={{ width: "100%", height: 140, objectFit: "cover", borderRadius: 4, marginBottom: 12 }}
                />
              )}
              <p style={{ fontWeight: 600, marginBottom: 4, fontSize: "0.95rem" }}>{r.title}</p>
              <p style={{ fontSize: "0.78rem", color: "var(--ink-muted)", marginBottom: 4 }}>
                {r.source_site}{r.total_time ? ` · ${r.total_time}` : ""}{r.cuisine ? ` · ${r.cuisine}` : ""}
              </p>
              {r.dietary_tags && (
                <span className="pill" style={{ fontSize: "0.7rem" }}>{r.dietary_tags}</span>
              )}
            </Link>
          ))}
        </div>
      )}

    </div>
  )
}