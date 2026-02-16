import Image from "next/image"

export default function Home() {
  return (
    <main style={{ padding: 20 }}>
      <h1>🍳 Recipe Search</h1>
      <p>Super cool cooking website</p>
	<div className="g-signin2" data-onsuccess="onSignIn"></div>
      <Image
        src="/Ramsey.jpg"
        alt="Gordon Ramsey"
        width={250}
        height={250}
      />
    </main>
  )
}

