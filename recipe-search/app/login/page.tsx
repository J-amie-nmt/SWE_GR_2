//login page
'use client'

import Image from "next/image"
import { useSession, signIn, signOut } from "next-auth/react"

export default function LoginPage() {
  const { data: session } = useSession()

  return (
    <div className="page-content fade-up" style={{ maxWidth: 440 }}>

      <span className="section-label">Account</span>
      <h1 style={{ fontSize: "2rem", marginBottom: 8, marginTop: 8 }}>Sign in</h1>
      <p style={{ marginBottom: 40, fontSize: "0.9rem" }}>
        Log in to save recipes and access your personal cookbook.
      </p>

      {session ? (
        // Signed in
        <div className="card" style={{ textAlign: "center" }}>
          <p style={{ marginBottom: 6, color: "var(--ink)", fontSize: "0.9rem" }}>
            Signed in as
          </p>
          <p style={{ color: "var(--accent)", fontWeight: 600, marginBottom: 24, fontSize: "1rem" }}>
            {session.user?.email}
          </p>
          <button className="btn btn-outline" onClick={() => signOut()}>
            Sign out
          </button>
        </div>
      ) : (
        // Signed out
        <div className="card">
          <p className="section-label" style={{ marginBottom: 16 }}>Continue with</p>
          <button
            onClick={() => signIn("google")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              width: "100%",
              padding: "12px 20px",
              background: "var(--bg-raised)",
              border: "1.5px solid var(--border)",
              borderRadius: 6,
              color: "var(--ink)",
              fontFamily: "'Sora', sans-serif",
              fontSize: "0.9rem",
              fontWeight: 400,
              cursor: "pointer",
              transition: "border-color 0.2s, background 0.2s",
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent)"
              ;(e.currentTarget as HTMLButtonElement).style.background = "var(--accent-dim)"
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)"
              ;(e.currentTarget as HTMLButtonElement).style.background = "var(--bg-raised)"
            }}
          >
            <Image src="/GoogleLogo.png" alt="Google" width={20} height={20} />
            Sign in with Google
          </button>
        </div>
      )}

    </div>
  )
}
