# recipe_search_scraper.py
"""
Recipe Search & Scraper Prototype
Searches for recipes across multiple websites and stores data in CSV
"""

from recipe_scrapers import scrape_html
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import time
from typing import List, Dict, Optional
from datetime import datetime
import re


class RecipeSearchScraper:
    """Search for recipes and scrape data from multiple sites"""
    
    def __init__(self):
        self.recipe_sites = [
            'allrecipes.com',
            'foodnetwork.com',
            'bonappetit.com',
            'epicurious.com',
            'seriouseats.com',
            'tasty.co',
            'simplyrecipes.com',
            'delish.com',
            'thekitchn.com',
            'food52.com'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.scraped_recipes = []
    
    def search_recipe_sites_directly(self, query: str, num_results: int = 20) -> List[str]:
        """
        Search directly on recipe sites
        
        Args:
            query: Search term
            num_results: Number of results to retrieve
            
        Returns:
            List of recipe URLs
        """
        print(f"\n🔍 Searching recipe sites for: '{query}'")
        
        recipe_urls = []
        
        # AllRecipes search
        print("  Searching AllRecipes...")
        recipe_urls.extend(self._search_allrecipes(query, 8))
        
        # Simply Recipes search
        print("  Searching Simply Recipes...")
        recipe_urls.extend(self._search_simplyrecipes(query, 6))
        
        # Bon Appetit search
        print("  Searching Bon Appetit...")
        recipe_urls.extend(self._search_bonappetit(query, 6))
        
        unique_urls = list(dict.fromkeys(recipe_urls))
        print(f"✓ Found {len(unique_urls)} recipe URLs")
        
        return unique_urls[:num_results]
    
    def _search_allrecipes(self, query: str, limit: int) -> List[str]:
        """Search AllRecipes.com"""
        try:
            search_url = f"https://www.allrecipes.com/search?q={quote_plus(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/recipe/' in href and 'allrecipes.com' in href:
                    clean_url = href.split('?')[0]  # Remove query params
                    if clean_url not in urls:  # Avoid duplicates
                        urls.append(clean_url)
                    if len(urls) >= limit:
                        break
            
            print(f"    Found {len(urls)} recipes from AllRecipes")
            return urls
        except Exception as e:
            print(f"    ⚠️ AllRecipes search failed: {str(e)}")
            return []
    
    def _search_simplyrecipes(self, query: str, limit: int) -> List[str]:
        """Search Simply Recipes"""
        try:
            search_url = f"https://www.simplyrecipes.com/search?q={quote_plus(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Simply Recipes recipe URLs have specific patterns
                if 'simplyrecipes.com' in href and (
                    ('-recipe-' in href and '/recipe/' not in href) or  # Older format
                    'how-to-make' in href or
                    'how-to-cook' in href
                ):
                    clean_url = href.split('?')[0]
                    # Must end with numbers (recipe ID)
                    if re.search(r'-\d+/?$', clean_url):
                        if clean_url not in urls:
                            urls.append(clean_url)
                        if len(urls) >= limit:
                            break
            
            print(f"    Found {len(urls)} recipes from Simply Recipes")
            return urls
        except Exception as e:
            print(f"    ⚠️ Simply Recipes search failed: {str(e)}")
            return []
    
    def _search_bonappetit(self, query: str, limit: int) -> List[str]:
        """Search Bon Appetit"""
        try:
            search_url = f"https://www.bonappetit.com/search?q={quote_plus(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/recipe/' in href:
                    if not href.startswith('http'):
                        href = f"https://www.bonappetit.com{href}"
                    clean_url = href.split('?')[0]
                    if clean_url not in urls:
                        urls.append(clean_url)
                    if len(urls) >= limit:
                        break
            
            print(f"    Found {len(urls)} recipes from Bon Appetit")
            return urls
        except Exception as e:
            print(f"    ⚠️ Bon Appetit search failed: {str(e)}")
            return []
    
    def _is_valid_recipe_url(self, url: str) -> bool:
        """Check if URL is a valid recipe page"""
        if not url.startswith('http'):
            return False
        
        # Filter out non-recipe pages
        invalid_patterns = [
            'google.com',
            'youtube.com',
            'pinterest.com',
            'facebook.com',
            '/search',
            '/category',
            '/tag',
            '/author',
            '/collections',
            '/gallery'
        ]
        
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False
        
        # Check if from known recipe sites
        domain = urlparse(url).netloc
        return any(site in domain for site in self.recipe_sites)
    
    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """
        Scrape a single recipe from URL
        
        Args:
            url: Recipe URL
            
        Returns:
            Dictionary with essential recipe data
        """
        try:
            # Fetch the page HTML
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Use recipe_scrapers with the HTML content
            scraper = scrape_html(html=response.content, org_url=url)
            
            # Extract essential data
            recipe_data = {
                'title': scraper.title(),
                'url': url,
                'author': self._safe_extract(scraper.author) or 'Unknown',
                'image_url': self._safe_extract(scraper.image) or '',
                'total_time': self._format_time(self._safe_extract(scraper.total_time)),
                'yields': self._safe_extract(scraper.yields) or '',
                'cuisine': self._safe_extract(scraper.cuisine) or '',
                'category': self._safe_extract(scraper.category) or '',
                'ingredients': ' | '.join(scraper.ingredients()),
                'instructions': self._clean_instructions(self._safe_extract(scraper.instructions)),
                'calories': self._extract_calories(scraper),
                'dietary_tags': ', '.join(self._extract_dietary_tags(scraper)),
                'source_site': urlparse(url).netloc,
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return recipe_data
            
        except Exception as e:
            print(f"✗ Failed to scrape {url}: {str(e)}")
            return None
    
    def _safe_extract(self, method):
        """Safely call scraper methods"""
        try:
            return method()
        except:
            return None
    
    def _format_time(self, time_val) -> str:
        """Format time to string"""
        if not time_val:
            return ''
        if isinstance(time_val, int):
            return f"{time_val} minutes"
        return str(time_val)
    
    def _clean_instructions(self, instructions: Optional[str]) -> str:
        """Clean and format instructions"""
        if not instructions:
            return ''
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', instructions)
        cleaned = cleaned.replace('\n\n', ' | ')
        cleaned = cleaned.strip()
        
        # Limit length for CSV
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + '...'
        
        return cleaned
    
    def _extract_calories(self, scraper) -> str:
        """Extract calorie information"""
        try:
            nutrients = scraper.nutrients()
            calories = nutrients.get('calories', '')
            if calories:
                # Clean up the calorie value
                return str(calories).replace('calories', '').strip()
            return ''
        except:
            return ''
    
    def _extract_dietary_tags(self, scraper) -> List[str]:
        """Extract dietary restriction tags"""
        tags = []
        
        try:
            ingredients = scraper.ingredients()
            ingredients_text = ' '.join(ingredients).lower()
            
            # Check for dietary markers
            if self._is_vegan(ingredients):
                tags.append('vegan')
            elif self._is_vegetarian(ingredients):
                tags.append('vegetarian')
            
            if 'gluten-free' in ingredients_text or 'gluten free' in ingredients_text:
                tags.append('gluten-free')
            
            if 'dairy-free' in ingredients_text or 'dairy free' in ingredients_text:
                tags.append('dairy-free')
            
            if any(word in ingredients_text for word in ['keto', 'low-carb', 'low carb']):
                tags.append('keto')
            
            if 'paleo' in ingredients_text:
                tags.append('paleo')
            
        except:
            pass
        
        return tags
    
    def _is_vegan(self, ingredients: List[str]) -> bool:
        """Check if recipe is vegan"""
        non_vegan = ['meat', 'chicken', 'beef', 'pork', 'fish', 'egg', 
                     'milk', 'cheese', 'butter', 'cream', 'honey', 'bacon',
                     'sausage', 'turkey', 'lamb', 'yogurt', 'gelatin']
        ingredients_text = ' '.join(ingredients).lower()
        return not any(item in ingredients_text for item in non_vegan)
    
    def _is_vegetarian(self, ingredients: List[str]) -> bool:
        """Check if recipe is vegetarian"""
        non_vegetarian = ['meat', 'chicken', 'beef', 'pork', 'fish', 
                         'bacon', 'sausage', 'turkey', 'lamb', 'anchovy',
                         'shrimp', 'crab', 'lobster', 'clam', 'oyster']
        ingredients_text = ' '.join(ingredients).lower()
        return not any(item in ingredients_text for item in non_vegetarian)
    
    def scrape_multiple(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        """
        Scrape multiple recipes with delay between requests
        
        Args:
            urls: List of recipe URLs
            delay: Delay in seconds between requests
            
        Returns:
            List of recipe dictionaries
        """
        recipes = []
        total = len(urls)
        
        print(f"\n📥 Starting to scrape {total} recipes...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] Scraping: {url}")
            
            recipe = self.scrape_recipe(url)
            if recipe:
                recipes.append(recipe)
                print(f"✓ Success: {recipe['title']}")
            
            # Be respectful with delays
            if i < total:
                time.sleep(delay)
        
        print(f"\n✓ Successfully scraped {len(recipes)} out of {total} recipes")
        return recipes
    
    def save_to_csv(self, recipes: List[Dict], filename: str = 'recipes.csv'):
        """
        Save recipes to CSV file
        
        Args:
            recipes: List of recipe dictionaries
            filename: Output CSV filename
        """
        if not recipes:
            print("⚠️  No recipes to save!")
            return
        
        # Define CSV columns (essential data)
        fieldnames = [
            'title',
            'url',
            'author',
            'source_site',
            'image_url',
            'total_time',
            'yields',
            'cuisine',
            'category',
            'calories',
            'dietary_tags',
            'ingredients',
            'instructions',
            'scraped_date'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for recipe in recipes:
                writer.writerow(recipe)
        
        print(f"\n💾 Saved {len(recipes)} recipes to '{filename}'")
        print(f"📊 File size: {self._get_file_size(filename)}")
    
    def _get_file_size(self, filename: str) -> str:
        """Get human-readable file size"""
        import os
        size = os.path.getsize(filename)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def search_and_scrape(self, query: str, num_results: int = 20, 
                         output_file: str = None) -> str:
        """
        Complete workflow: search, scrape, and save to CSV
        
        Args:
            query: Search term
            num_results: Number of recipes to scrape
            output_file: Output CSV filename (auto-generated if None)
            
        Returns:
            Output filename
        """
        # Search for recipe URLs
        urls = self.search_recipe_sites_directly(query, num_results)
        
        if not urls:
            print("⚠️  No recipe URLs found!")
            return None
        
        # Scrape recipes
        recipes = self.scrape_multiple(urls, delay=1.5)
        
        if not recipes:
            print("⚠️  No recipes successfully scraped!")
            return None
        
        # Generate filename if not provided
        if output_file is None:
            safe_query = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"recipes_{safe_query}_{timestamp}.csv"
        
        # Save to CSV
        self.save_to_csv(recipes, output_file)
        
        return output_file


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("🍳 RECIPE SEARCH & SCRAPER PROTOTYPE")
    print("="*60)
    
    # Initialize scraper
    scraper = RecipeSearchScraper()
    
    # Example 1: Search and scrape chocolate chip cookies
    print("\n" + "="*60)
    print("EXAMPLE 1: Chocolate Chip Cookies")
    print("="*60)
    scraper.search_and_scrape(
        query="chocolate chip cookies",
        num_results=15,
        output_file="chocolate_chip_cookies.csv"
    )
    
    # Example 2: Search for pasta recipes
    print("\n" + "="*60)
    print("EXAMPLE 2: Pasta Carbonara")
    print("="*60)
    scraper.search_and_scrape(
        query="pasta carbonara",
        num_results=15,
        output_file="pasta_carbonara.csv"
    )
    
    print("\n" + "="*60)
    print("✓ ALL DONE! Check your CSV files.")
    print("="*60)