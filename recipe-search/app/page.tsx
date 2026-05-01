'use client'
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const SITE_NAME = "Dr.Dan's Cookbook"
const HERO = {
  tagline: "Find and save recipes from across the web",
  description: "If you have ever found yourself trying to find something to do with a random assortment of ingredients this website is for you. Using our webscraper we created a evergrowing recipe database from popular recipes from across the web.",
  ctaText: "Search Recipes Quickly",
  ctaLink: "/search",
}

export default function Home() {
  const [recipeCount, setRecipeCount] = useState<number | null>(null)
  const [scrapeCount, setScrapeCount] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/stats')
      .then(res => res.json())
      .then(({ recipeCount, scrapeCount }) => {
        setRecipeCount(recipeCount)
        setScrapeCount(scrapeCount)
      })
  }, [])

  const STATS = [
    { number: recipeCount ?? '...', label: "Recipes in the database" },
    { number: 120,                  label: "Recipe sites scraped" },
    { number: scrapeCount ?? '...', label: "Scrapes Ran" },
  ]

  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh" }}>
      {/* HERO */}
      <section className="fade-up" style={{
        maxWidth: 700, margin: "0 auto",
        padding: "100px 32px 80px",
        textAlign: "center",
      }}>
        <h1 style={{
          fontFamily: "'Fraunces', serif",
          fontSize: "clamp(2.4rem, 5vw, 4rem)",
          fontWeight: 700, lineHeight: 1.1,
          letterSpacing: "-1.5px",
          color: "var(--ink)",
          marginBottom: 20,
        }}>
          {HERO.tagline}
        </h1>
        <p style={{ fontSize: "1rem", maxWidth: 500, margin: "0 auto 36px", color: "var(--ink-muted)" }}>
          {HERO.description}
        </p>
        <a href={HERO.ctaLink} className="btn">{HERO.ctaText}</a>
      </section>

      <hr className="divider" style={{ maxWidth: 880, margin: "0 auto" }} />

      {/* STATS */}
      <div style={{
        maxWidth: 880, margin: "0 auto",
        padding: "0 32px 80px",
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 1, background: "var(--border)",
        border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden",
      }}>
        {STATS.map((s, i) => (
          <div key={i} style={{ background: "var(--bg-card)", padding: "29px 35px" }}>
            <span style={{
              display: "block",
              fontFamily: "'Fraunces', serif",
              fontSize: "2rem", fontWeight: 700,
              color: "var(--accent)", letterSpacing: "-1px",
              marginBottom: 4,
            }}>{s.number}</span>
            <span style={{ fontSize: "0.78rem", color: "var(--ink-muted)" }}>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
