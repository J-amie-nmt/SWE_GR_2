//Home page
const SITE_NAME = "Dr.Dans's Cookbook"

const HERO = {
  tagline: "Find recipes based on basic filters",
  description: "If you have ever found yourself trying to find something to do with a random assortment of ingredients this website is for you. Using our webscraper we compiled a various recipe catalog that you can search with a wide variety of filters. ",
  ctaText: "Search Recipes Quickly",
  ctaLink: "/recipes",
}

const ABOUT = {
  heading: "About This Website",
  paragraphs: [
    "This website was made by a group of software engineers who were trying to make a website that will store various recipe types while allowing users to search for them based on certain qualities of the dish. This website was created in Next.js and the front end devs designed and stylized most of the features. If you would like to find out more about the developers we have an about page link at the top of the website :) ",
    "Actual funcionality of the website here maybe?",
  ],
}

const STATS = [
  { number: "X many", label: "Stat with amount of recipes" },
  { number: "X many", label: "Stat with amount of filters" },
  { number: "X many", label: "Some other stat" },
]

export default function Home() {
  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh" }}>

      {/* HERO */}
      <section className="fade-up" style={{
        maxWidth: 700, margin: "0 auto",
        padding: "100px 32px 80px",
        textAlign: "center",
      }}>
        <span className="pill" style={{ marginBottom: 28, display: "inline-block" }}>
          {SITE_NAME}
        </span>
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
          <div key={i} style={{ background: "var(--bg-card)", padding: "28px 32px" }}>
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
