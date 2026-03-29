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
  	overflowX: "auto",
  	whiteSpace: "nowrap",
  	scrollbarWidth: "none",
     }}>
  <Link href="/" style={{ marginRight: "0.53rem", display: "flex", alignItems: "center", flexShrink: 0 }}>
  <DCBLogo />
  </Link>
  <Link href="/" className="nav-pill">Home</Link>
  <Link href="/search" className="nav-pill">Search Recipes</Link>
  <Link href="/saved" className="nav-pill">Saved Recipes</Link>
  <Link href="/about" className="nav-pill">About</Link>
  <Link href="/login" className="nav-pill nav-pill--accent" style={{ marginLeft: "auto", flexShrink: 0 }}>Login</Link>
</nav>
  )
}
