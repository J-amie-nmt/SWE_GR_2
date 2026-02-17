'use client'

import { useState } from 'react';

export default function AboutPage() {
  return (
    <main style={{ padding: 40 }}>
      <h1>About us:</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-15">
	<div className="bg-black rounded-xl shadow-lg p-6 hover:shadow-2xl transition-shadow">
	<h3 className="text-xl font-bold mb-2">Tristan Coull</h3>
	<p className="text-white-600">Something</p>
	</div>
	<div className="bg-black rounded-xl shadow-lg p-6 hover:shadow-2xl transition-shadow">
	<h3 className="text-xl font-bold mb-2">Caelan Eakman</h3>
	<p className="text-white-600">Something</p>
	</div>
	<div className="bg-black rounded-xl shadow-lg p-6 hover:shadow-2xl transition-shadow">
	<h3 className="text-xl font-bold mb-2">Jamie Farrow</h3>
	<p className="text-white-600">Something</p>
	</div>
	<div className="bg-black rounded-xl shadow-lg p-6 hover:shadow-2xl transition-shadow">
	<h3 className="text-xl font-bold mb-2">Miles Taylor</h3>
	<p className="text-white-600">Something</p>
	</div>
	<div className="bg-black rounded-xl shadow-lg p-6 hover:shadow-2xl transition-shadow">
	<h3 className="text-xl font-bold mb-2">Amin Weinman</h3>
	<p className="text-white-600">Something</p>
	</div>
</div>
      <p></p>
    </main>
  )
}
