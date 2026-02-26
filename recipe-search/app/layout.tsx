// layout page
import "./globals.css"
import "./theme.css"   //
import Nav from "./components/Nav"
import { Providers } from './providers'

export const metadata = {
  title: "Dr.Dans Cookbook",
  description: "Find and save recipes from anywhere",
}
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Nav />
          {children}
          <footer style={{
            textAlign: "center",
            padding: "20px 32px",
            borderTop: "1px solid var(--border)",
            marginTop: "48px",
            fontSize: "0.75rem",
            color: "var(--ink-muted)",
            background: "var(--bg)",
          }}>
            {new Date().getFullYear()} Dr.Dans Cookbook
          </footer>
        </Providers>
      </body>
    </html>
  )
}
