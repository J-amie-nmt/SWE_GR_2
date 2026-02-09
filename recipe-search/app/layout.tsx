import "./globals.css"
import Nav from "./components/Nav"

export const metadata = {
  title: "Recipe Search",
  description: "Find and save recipes from anywhere",
}
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        <Nav />
        <main style={{ padding: "2rem" }}>
          {children}
        </main>
        <footer style={{
          textAlign: "center",
          padding: "1rem",
          borderTop: "1px solid #ddd",
          marginTop: "2rem"
        }}>
          © {new Date().getFullYear()} Recipe Search
        </footer>
      </body>
    </html>
  )
}
