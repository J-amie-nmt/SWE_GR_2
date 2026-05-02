//app/search/page.tsx
//search page of website where users can search through tags or input text
'use client'
import { useState, useEffect, useCallback } from 'react'
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

interface FilterOptions {
  cuisines: string[]
  diets: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const PAGE_SIZE = 21

export default function RecipesPage() {
  const [text, setText] = useState('')
  const [results, setResults] = useState<RecipeSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  // Filter state
  const [cuisine, setCuisine] = useState('')
  const [diet, setDiet] = useState('')
  const [maxTime, setMaxTime] = useState<number | null>(null)
  const [sort, setSort] = useState<'newest' | 'title' | 'time'>('newest')
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ cuisines: [], diets: [] })

  // Fetch filter options upon mount
  useEffect(() => {
    fetch(`${API_BASE}/api/recipes/filters`)
      .then(r => r.json())
      .then(setFilterOptions)
      .catch(console.error)
  }, [])

  const fetchRecipes = useCallback(async (query: string, pageNum: number) => {
    setLoading(true)
    setError(null)
    
    const offset = (pageNum - 1) * PAGE_SIZE
    try {
      const params = new URLSearchParams({
        q: query,
        limit: String(PAGE_SIZE),
        offset: String(offset),
        sort,
      })
      if (cuisine) params.set('cuisine', cuisine)
      if (diet) params.set('diet', diet)
      if (maxTime) params.set('max_time', String(maxTime))
      
      const res = await fetch(`${API_BASE}/api/recipes?${params}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data)) {
        setResults(data)
        setTotal(data.length)
      } else {
        setResults(data.results || [])
        setTotal(data.total || 0)
      }
    } catch (err) {
      console.error(err)
      setError("Something went wrong please try again.")
    } finally {
      setLoading(false)
    }
  }, [cuisine, diet, maxTime, sort])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    setSearched(true)
    setPage(1)
    fetchRecipes(text.trim(), 1)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    fetchRecipes(text.trim(), newPage)
  }

  // Re-run search when filters change (only if a search has already been made)
  useEffect(() => {
    if (searched && text.trim()) {
      setPage(1)
      fetchRecipes(text.trim(), 1)
    }
  }, [cuisine, diet, maxTime, sort])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="page-content fade-up">
      <span className="section-label">Discover</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 8 }}>
        Recipe Search
      </h1>
      <p style={{ marginBottom: 40, fontSize: "0.95rem", maxWidth: 500 }}>
        Search by cuisine type, time to cook, dietary preferences, and more.
      </p>

      <form onSubmit={handleSearch} style={{ display: "flex", maxWidth: 560, marginBottom: 16 }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. pasta, vegetarian, gluten-free"
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 40, maxWidth: 560 }}>
        <select
          value={cuisine}
          onChange={e => setCuisine(e.target.value)}
        >
          <option value="">All cuisines</option>
          {filterOptions.cuisines.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select
          value={diet}
          onChange={e => setDiet(e.target.value)}
        >
          <option value="">All diets</option>
          {filterOptions.diets.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>

        <select
          value={maxTime ?? ''}
          onChange={e => setMaxTime(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Any time</option>
          <option value="15">Under 15 min</option>
          <option value="30">Under 30 min</option>
          <option value="60">Under 1 hour</option>
        </select>

        <select
          value={sort}
          onChange={e => setSort(e.target.value as typeof sort)}
        >
          <option value="newest">Newest</option>
          <option value="title">A–Z</option>
          <option value="time">Quickest</option>
        </select>
      </div>

      <hr className="divider" style={{ marginBottom: 48 }} />

      {error && (
        <p style={{ color: "var(--red, red)", marginBottom: 24 }}>{error}</p>
      )}

      {!loading && searched && !error && results.length === 0 && (
        <p style={{ color: "var(--ink-muted)" }}>
          No recipes found for <strong>"{text}"</strong>.
        </p>
      )}

      {!loading && results.length > 0 && (
        <>
          <p style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginBottom: 20 }}>
            Page {page} of {totalPages || 1} &mdash; {total} results
          </p>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: 16
          }}>
            {results.map((r) => (
              <Link key={r.id} href={`/search/${r.id}`} className="card">
                {r.image_url && (
                  <img
                    src={r.image_url}
                    alt={r.title}
                    style={{ width: "100%", height: 140, objectFit: "cover" }}
                    onError={(e) => { e.currentTarget.style.display = 'none' }}
                  />
                )}
                <div style={{ padding: "10px 4px 4px" }}>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: "0.92rem" }}>
                    {r.title}
                  </p>

                  {r.source_site && (
                    <p style={{
                      margin: "4px 0 0",
                      fontSize: "0.78rem",
                      color: "var(--ink-muted)"
                    }}>
                      {r.source_site}
                    </p>
                  )}

                  <div style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 4,
                    marginTop: 8
                  }}>
                    {r.total_time && <span className="pill">{r.total_time}</span>}
                    {r.cuisine && <span className="pill">{r.cuisine}</span>}
                    {r.dietary_tags?.split(',').slice(0, 2).map((t) => (
                      <span key={t} className="pill">{t.trim()}</span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div style={{
              marginTop: 32,
              display: "flex",
              flexWrap: "wrap",
              gap: 8
            }}>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => handlePageChange(p)}
                  className="btn"
                  style={{
                    background: p === page ? "var(--accent)" : "transparent",
                    color: p === page ? "#fff" : "inherit"
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
