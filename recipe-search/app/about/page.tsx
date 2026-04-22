'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

interface ScrapeRequest {
  id: number
  query: string
  submitted_by: string
  status: string
  created_at: string
}

export default function RequestPage() {
  const { data: session, status } = useSession()

  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const [history, setHistory] = useState<ScrapeRequest[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const fetchHistory = async (email: string) => {
    setHistoryLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/scrape-requests?email=${encodeURIComponent(email)}`)
      if (!res.ok) throw new Error()
      setHistory(await res.json())
    } catch {
      // non-critical
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    if (session?.user?.email) fetchHistory(session.user.email)
  }, [session])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || !session?.user?.email) return

    setLoading(true)
    setSubmitError(null)
    setSubmitSuccess(false)

    try {
      const res = await fetch(`${API_BASE}/api/scrape-requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          submitted_by: session.user.email,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setSubmitError(data.detail ?? "Something went wrong. Please try again.")
        return
      }

      setSubmitSuccess(true)
      setQuery('')
      fetchHistory(session.user.email)
    } catch {
      setSubmitError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit(e as unknown as React.FormEvent)
  }

  return (
    <div className="page-content fade-up">
      <span className="section-label">Community</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 8 }}>
        Request Recipes
      </h1>
      <p style={{ marginBottom: 40, fontSize: "0.95rem", maxWidth: 500 }}>
        Suggest a cuisine, ingredient, or dish and we'll scrape new recipes for it on our next update. You can submit up to 3 requests per week.
      </p>

      {status === 'loading' && (
       <p style={{ color: "var(--ink-muted)", fontSize: "0.9rem" }}>Loading...</p>
	)}

      {status === 'unauthenticated' && (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.9rem" }}>
          Please <a href="/login" style={{ color: "var(--accent)" }}>sign in</a> to submit recipe requests.
        </p>
      )}

      {status === 'authenticated' && session && (
        <>
          <form onSubmit={handleSubmit} style={{ display: "flex", maxWidth: 560, marginBottom: 12 }}>
            <input
              type="text"
              value={query}
              onChange={e => { setQuery(e.target.value); setSubmitSuccess(false); setSubmitError(null) }}
              onKeyDown={handleKeyDown}
              placeholder="e.g. Sausage rolls, Chocolate Cake, Carrot Juice"
              style={{ flex: 1 }}
              disabled={loading}
              maxLength={200}
            />
            <button type="submit" className="btn" disabled={loading || !query.trim()}>
              {loading ? "Submitting...." : "Submit"}
            </button>
          </form>

          {submitSuccess && (
            <p style={{ fontSize: "0.85rem", color: "var(--accent)", marginBottom: 24 }}>
            Request submitted! It will be picked up on the next scrape run.
            </p>
          )}
          {submitError && (
            <p style={{ fontSize: "0.85rem", color: "var(--red, red)", marginBottom: 24 }}>
              {submitError}
            </p>
          )}

          <hr className="divider" style={{ marginBottom: 40, marginTop: 24 }} />

          <span className="section-label" style={{ marginBottom: 20, display: "block" }}>
            Your previous requests
          </span>

          {historyLoading && (
            <p style={{ color: "var(--ink-muted)", fontSize: "0.9rem" }}>Loading history...</p>
          )}

          {!historyLoading && history.length === 0 && (
            <p style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
              No requests yet — submit one above!
            </p>
          )}

          {!historyLoading && history.length > 0 && (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: 16,
            }}>
              {history.map((req) => (
                <div key={req.id} className="card">
                  <div style={{
                    width: 36, height: 36, borderRadius: "50%",
                    background: "var(--accent-dim)",
                    border: "1.5px solid var(--accent)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "0.78rem", fontWeight: 600, color: "var(--accent)",
                    marginBottom: 12,
                  }}>
                    {req.status === 'done' ? '✓' : req.status === 'error' ? '✕' : '…'}
                  </div>

                  <p style={{ margin: 0, fontWeight: 600, fontSize: "0.92rem", color: "var(--ink)" }}>
                    {req.query}
                  </p>

                  <span style={{
                    fontSize: "0.68rem", fontWeight: 600,
                    textTransform: "uppercase", letterSpacing: "1px",
                    color: "var(--accent)", display: "block", marginTop: 6, marginBottom: 8,
                  }}>
                    {req.status}
                  </span>

                  <p style={{ fontSize: "0.78rem", color: "var(--ink-muted)", margin: 0 }}>
                    {new Date(req.created_at).toLocaleDateString(undefined, {
                      year: 'numeric', month: 'short', day: 'numeric',
                    })}
                  </p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
