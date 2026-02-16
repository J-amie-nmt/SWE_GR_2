'use client'
import { useState } from 'react';

export default function RecipesPage() {
  const [text, setText] = useState('')
  
  return (
    <main style={{ padding: 40 }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter your recipe"
        className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
      />
      <h1> </h1>
      <p></p>
    </main>
  )
}
