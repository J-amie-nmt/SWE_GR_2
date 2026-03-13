"use client"
import Link from "next/link"
import DCBLogo from "./DCBLogo"

export default function Nav() {
  return (
    <nav style={{
      padding: "0.75rem 1.5rem",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      background: "var(--bg)",
      position: "relative",
    }}>
      <Link href="/" style={{ marginRight: "0.53rem", display: "flex", alignItems: "center" }}>
        <DCBLogo />
      </Link>
      <Link href="/" className="nav-pill">Home</Link>
      <Link href="/search" className="nav-pill">Search Recipes</Link>
      <Link href="/saved" className="nav-pill">Saved Recipes</Link>
      <Link href="/about" className="nav-pill">About</Link>
      <div style={{ position: "absolute", top: "50%", right: "1rem", transform: "translateY(-50%)" }}>
        <Link href="/login" className="nav-pill nav-pill--accent">Login</Link>
      </div>
    </nav>
  )
}
