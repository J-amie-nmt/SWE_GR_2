import { createClient } from '@supabase/supabase-js'
import { NextResponse } from 'next/server'

//Supabase Route
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!  // server only, never exposed
)

export async function GET() {
  const [recipes, scrapes] = await Promise.all([
    supabase.from('Recipes').select('id').order('id', { ascending: false }).limit(1).single(),
    supabase.from('search_log').select('id').order('id', { ascending: false }).limit(1).single(),
  ])

  return NextResponse.json({
    recipeCount: recipes.data?.id ?? 0,
    scrapeCount: scrapes.data?.id ?? 0,
  })
}