'use client'

import { useSession, signIn, signOut } from "next-auth/react"

export default function LoginPage()
{
  const { data: session } = useSession()

  return (
    <main style={{ padding: 40 }}>
      <h1> Login </h1>
      <p>Google Login: </p>
      
      {session ? (
        <div>
          <p>Signed in as {session.user?.email}</p>
          <button onClick={() => signOut()}>Sign out</button>
        </div>
      ) : (
        <button onClick={() => signIn("google")}>Sign in with Google</button>
      )}
    </main>
  )
}
