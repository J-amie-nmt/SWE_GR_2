// app/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'



const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

const SITE_NAME = "Dr.Dan's Cookbook"

const HERO = {
  tagline: "Find recipes based on basic searches",
  description: "If you have ever found yourself trying to find something to do with a random assortment of ingredients this website is for you. Using our webscraper we compiled a various recipe catalog that you can search with a wide variety of filters.",
  ctaText: "Search Recipes Quickly",
  ctaLink: "/search",
}

const ABOUT = {
  heading: "About This Website",
  paragraphs: [
    "This website was made by a group of software engineers who were trying to make a website that will store various recipe types while allowing users to search for them based on certain qualities of the dish. This website was created in Next.js and the front end devs designed and stylized most of the features. If you would like to find out more about the developers we have an about page link at the top of the website :)",
    "Our future plans for the website include pushing it to be hosted by vercel. When hosted by vercel we plan to create a flask server that will run our database interpreter and our webscraper that pulls recipes. We also plan to move our database to supabase.",
  ],
}

export default function Home() {
  const [recipeCount, setRecipeCount] = useState<number | null>(null)
  const [scrapeCount, setScrapeCount] = useState<number | null>(null)

useEffect(() => {
supabase
  .from('Recipes')
  .select('id')
  .order('id', { ascending: false })
  .limit(1)
  .single()
  .then(({ data, error }) => {
    console.log('Last recipe id:', data, error)
    setRecipeCount(data?.id ?? 0)
  })

supabase
  .from('search_log')
  .select('id')
  .order('id', { ascending: false })
  .limit(1)
  .single()
  .then(({ data, error }) => {
    console.log('Last recipe id:', data, error)
    setRecipeCount(data?.id ?? 0)
  })
}, [])

  const STATS = [
    { number: recipeCount ?? '...', label: "Recipes in the catalog" },
    { number: 120,                  label: "Recipe sites scraped" },
    { number: scrapeCount ?? '...', label: "Number of scrapes run" },
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

      {/* ABOUT */}
      <section style={{
        maxWidth: 880, margin: "0 auto",
        padding: "80px 32px",
        display: "grid",
        gridTemplateColumns: "180px 1fr",
        gap: 64,
      }}>
        <div className="section-label" style={{ paddingTop: 4 }}>About</div>
        <div>
          <h2 style={{
            fontFamily: "'Fraunces', serif",
            fontSize: "1.8rem", fontWeight: 400,
            letterSpacing: "-0.3px", marginBottom: 20,
            color: "var(--ink)",
          }}>
            {ABOUT.heading}
          </h2>
          {ABOUT.paragraphs.map((p, i) => (
            <p key={i} style={{ marginBottom: 14, fontSize: "0.93rem" }}>{p}</p>
          ))}
        </div>
      </section>

      {/* STATS */}
      <div style={{
        maxWidth: 880, margin: "0 auto",
        padding: "0 32px 80px",
        display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
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
