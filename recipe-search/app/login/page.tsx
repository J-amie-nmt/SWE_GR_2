'use client'
import Image from "next/image"
import { useSession, signIn, signOut } from "next-auth/react"

export default function LoginPage()
{
  const { data: session } = useSession()

  return (
    <main style={{ padding: 40 }}>
    
      <h1> Login </h1>
      <p>Google Login: </p>
      <div className="flex items-center py-3 ">
  	<span className="px-3 py-5 bg-white text-black rounded-full text-sm font-medium flex 		 items-center gap-1">
    <Image
      src="/GoogleLogo.png"
      alt="Google Logo"
      width={25}
      height={25}
    />
    {session ? (
      <div className="flex items-center gap-2">
        <p>Signed in as {session.user?.email}</p>
        <button onClick={() => signOut()}>Sign out</button>
      </div>
    ) : (
      <button onClick={() => signIn("google")}>Sign in with Google</button>
    )}
  </span>
</div>
    </main>
  )
}
