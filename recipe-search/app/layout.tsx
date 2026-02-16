import "./globals.css"
import Nav from "./components/Nav"
import { Providers } from './providers'

export const metadata = {
  title: "Shins Cookbook",
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
        <Providers>
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
            © {new Date().getFullYear()} Shins Cookbook
          </footer>
        </Providers>
      </body>
    </html>
  )
}
