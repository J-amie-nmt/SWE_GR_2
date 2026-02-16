import Image from "next/image"

export default function Home() {
  return (
    <main style={{ padding: 20 }}>
    <button className="px-15 py-4 bg-green-500 text-white rounded-lg"/>
      <h1>🍳Shins Cookbook</h1>
      <p>Welcome to the recipe search website!</p>
      <p>On this website you can search for specific recipes based on origin of food, rating of food, ingredient information, and many other specific flags you can search based on.</p>
      <Image
        src="/Ramsey.jpg"
        alt="Gordon Ramsey"
        width={250}
        height={250}
      />
    </main>
  )
}

