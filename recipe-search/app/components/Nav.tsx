"use client"

import Link from "next/link"
import DCBLogo from "./DCBLogo"

export default function Nav() {
  return (
    <nav style={{ padding: "1rem", borderBottom: "1px solid #ddd" }}>
      <Link href="/"><DCBLogo/></Link>
      <Link href="/">Home</Link>{" "}
      <Link href="/recipes">Recipes</Link>{" "}
      <Link href="/about">About</Link>{" "}
      <div className="absolute top-4 right-4">
      <Link href="/login">Login</Link>
      </div>
    </nav>
  )
}
