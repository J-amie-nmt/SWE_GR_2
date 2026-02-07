"use client"

import Link from "next/link"

export default function Nav() {
  return (
    <nav style={{ padding: "1rem", borderBottom: "1px solid #ddd" }}>
      <strong>🍳 Recipe Search</strong>{" "}
      <Link href="/">Home</Link>{" "}
      <Link href="/recipes">Recipes</Link>
    </nav>
  )
}
