'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

interface SavedRecipe {
  recipe_id:   number
  title:       string
  source_site: string
  image_url:   string
  total_time:  string
  cuisine:     string
  dietary_tags: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export default function SavedPage() {
  const { data: session, status } = useSession()
  const [recipes, setRecipes]     = useState<SavedRecipe[]>([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    if (status === 'loading') return
    if (!session?.user?.email) { setLoading(false); return }

    fetch(`${API_BASE}/api/saved?email=${encodeURIComponent(session.user.email)}`)
      .then(r => r.json())
      .then(data => { setRecipes(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [session, status])

  // Not logged in
  if (status !== 'loading' && !session) return (
    <div className="page-content fade-up">
      <span className="section-label">Your Cookbook</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 16 }}>
        Saved Recipes
      </h1>
      <p style={{ color: "var(--ink-muted)" }}>
        Please <Link href="/login" style={{ color: "var(--accent)" }}>sign in</Link> to see your saved recipes.
      </p>
    </div>
  )

  return (
    <div className="page-content fade-up">
      <span className="section-label">Your Cookbook</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 32 }}>
        Saved Recipes
      </h1>

      {/* Loading skeletons */}
      {loading && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="card" style={{ opacity: 0.4 }}>
              <div style={{ height: 140, borderRadius: 4, background: "var(--border)", marginBottom: 12 }} />
              <div style={{ height: 12, borderRadius: 4, background: "var(--border)", marginBottom: 8 }} />
              <div style={{ height: 8, borderRadius: 4, background: "var(--border)", width: "60%" }} />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && recipes.length === 0 && (
        <p style={{ color: "var(--ink-muted)" }}>
          No saved recipes yet —{' '}
          <Link href="/search" style={{ color: "var(--accent)" }}>
            search for something delicious
          </Link>.
        </p>
      )}

      {/* Recipe grid */}
      {!loading && recipes.length > 0 && (
        <>
          <p style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginBottom: 20 }}>
            {recipes.length} saved recipe{recipes.length !== 1 ? 's' : ''}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
            {recipes.map(r => (
              <Link key={r.recipe_id} href={`/search/${r.recipe_id}`} className="card">
                {r.image_url && (
                  <img src={r.image_url} alt={r.title}
                    style={{ width: "100%", height: 140, objectFit: "cover" }}
                    onError={e => { e.currentTarget.style.display = 'none' }}
                  />
                )}
                <div style={{ padding: "10px 4px 4px" }}>
                  <p style={{ margin: 0, fontWeight: 600, fontSize: "0.92rem" }}>{r.title}</p>
                  {r.source_site && (
                    <p style={{ margin: "4px 0 0", fontSize: "0.78rem", color: "var(--ink-muted)" }}>
                      {r.source_site}
                    </p>
                  )}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                    {r.total_time   && <span className="pill">{r.total_time}</span>}
                    {r.cuisine      && <span className="pill">{r.cuisine}</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
