// About page
'use client'


const TEAM = [
  { name: "Tristan Coull",  role: "Team Lead", bio: "Short bio here." },
  { name: "Caelan Eakman",  role: "Front-end Dev", bio: "Short bio here." },
  { name: "Jamie Farrow",   role: "Back-end Dev", bio: "Short bio here." },
  { name: "Miles Taylor",   role: "Back-end Dev", bio: "Short bio here." },
  { name: "Amin Weinman",   role: "Front-end Dev", bio: "Short bio here." },
]


export default function AboutPage() {
  return (
    <div className="page-content fade-up">

      {/*Header*/}
      <span className="section-label">The project</span>
      <h1 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginTop: 8, marginBottom: 16 }}>
        Team Information
      </h1>
      <p style={{ maxWidth: 560, marginBottom: 64, fontSize: "0.95rem" }}>
        Team intro something something
      </p>

      <hr className="divider" style={{ marginBottom: 64 }} />

      {/* Team members*/}
      <span className="section-label" style={{ marginBottom: 24, display: "block" }}>Meet the team</span>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
        gap: 16,
      }}>
        {TEAM.map((dev) => (
          <div key={dev.name} className="card">
            {/*Titles*/}
            <div style={{
              width: 44, height: 44, borderRadius: "50%",
              background: "var(--accent-dim)",
              border: "1.5px solid var(--accent)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "0.85rem", fontWeight: 600, color: "var(--accent)",
              marginBottom: 16,
            }}>
              {dev.name.split(" ").map((n: string) => n[0]).join("")}
            </div>

            {/* Name*/}
            <h3 style={{ fontSize: "1.05rem", marginBottom: 4, color: "var(--ink)" }}>
              {dev.name}
            </h3>

            {/* Roles */}
            <span style={{
              fontSize: "0.68rem", fontWeight: 600,
              textTransform: "uppercase", letterSpacing: "1px",
              color: "var(--accent)", display: "block", marginBottom: 12,
            }}>
              {dev.role}
            </span>

            {/* Bios */}
            <p style={{ fontSize: "0.82rem", lineHeight: 1.7 }}>
              {dev.bio}
            </p>
          </div>
        ))}
      </div>

    </div>
  )
}
