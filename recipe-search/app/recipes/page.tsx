//Recipe search page
'use client'

import { useState } from 'react';

export default function RecipesPage() {
  const [text, setText] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // wire up your scraper/API call here using `text`
    console.log("Searching for:", text)
  }

  return (
    <div className="page-content fade-up">

      {/* HEADING */}
      <span className="section-label">Discover</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 8 }}>
        Recipe Search
      </h1>
      <p style={{ marginBottom: 40, fontSize: "0.95rem", maxWidth: 500 }}>
        Search be ingredients, cuisine type, dietary preferences, and ratings!
      </p>

      {/* SEARCH BAR */}
      <form onSubmit={handleSearch} style={{ display: "flex", gap: 0, maxWidth: 560, marginBottom: 48 }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. 3 Onions, American, Low Carb"
          style={{
            flex: 1,
            borderRadius: "4px 0 0 4px",
            borderRight: "none",
          }}
        />
        <button
          type="submit"
          className="btn"
          style={{ borderRadius: "0 4px 4px 0", whiteSpace: "nowrap" }}
        >
          Search
        </button>
      </form>

      <hr className="divider" style={{ marginBottom: 48 }} />

      {/* RESULTS AREA */}
      <span className="section-label" style={{ marginBottom: 20, display: "block" }}>Results</span>

      {/* 
        TODO: Replace this placeholder grid with your actual recipe results.
        Map over your results array and render a .card for each recipe.

        Example structure:
        results.map(recipe => (
          <div key={recipe.id} className="card">
            <h3>{recipe.title}</h3>
            <p>{recipe.description}</p>
          </div>
        ))
      */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
        gap: 16,
      }}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card" style={{ opacity: 0.4 }}>
            <div style={{
              height: 12, borderRadius: 4,
              background: "var(--border)", marginBottom: 12,
            }} />
            <div style={{
              height: 8, borderRadius: 4,
              background: "var(--border)", marginBottom: 8, width: "70%",
            }} />
            <div style={{
              height: 8, borderRadius: 4,
              background: "var(--border)", width: "50%",
            }} />
          </div>
        ))}
      </div>

    </div>
  )
}
