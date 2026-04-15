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

  const fetchRecipes = async (query: string, pageNum: number) => {
    setLoading(true)
    setError(null)

    const offset = (pageNum - 1) * PAGE_SIZE

    try {
      const url = `${API_BASE}/api/recipes?q=${encodeURIComponent(query)}&limit=${PAGE_SIZE}&offset=${offset}`
      const res = await fetch(url)

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }

      const data = await res.json()

      // Supports both {results, total} OR plain array fallback
      if (Array.isArray(data)) {
        setResults(data)
        setTotal(data.length)
      } else {
        setResults(data.results || [])
        setTotal(data.total || 0)
      }

    } catch (err) {
      console.error(err)
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

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

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="page-content fade-up">
      <span className="section-label">Discover</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 8 }}>
        Recipe Search
      </h1>
      <p style={{ marginBottom: 40, fontSize: "0.95rem", maxWidth: 500 }}>
        Search by ingredients, cuisine type, dietary preferences, and more!
      </p>

      <form onSubmit={handleSearch} style={{ display: "flex", maxWidth: 560, marginBottom: 48 }}>
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
            Page {page} of {totalPages || 1}
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

          {/* Pagination Controls */}
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
