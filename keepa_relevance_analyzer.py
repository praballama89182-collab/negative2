import requests
import pandas as pd
from datetime import datetime

class KeepaRelevanceAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.keepa.com/product"
        self.product_cache = {} [cite: 7]

    def fetch_product_data(self, asin):
        """Fetch product details from Keepa API."""
        if asin in self.product_cache:
            return self.product_cache[asin] [cite: 8, 9, 10]
        
        params = {'key': self.api_key, 'asin': asin, 'domain': 1}
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json() [cite: 12, 13, 14, 15, 16]
            
            if data and 'products' in data and data['products']:
                product = data['products'][0]
                self.product_cache[asin] = product
                return product [cite: 19]
        except Exception as e:
            print(f"Error fetching ASIN {asin}: {e}") [cite: 22]
        return None

    def extract_keywords(self, product_data):
        """Extracts brand, title, and category words for matching."""
        keywords = set()
        if not product_data: return keywords [cite: 26]
        
        for field in ['title', 'brand']:
            if field in product_data:
                keywords.update(str(product_data[field]).lower().split()) [cite: 27, 36, 37]
        
        if 'categoryTree' in product_data:
            for cat in product_data['categoryTree']:
                keywords.update(str(cat.get('name', '')).lower().split()) [cite: 28, 29, 30, 31]
        return keywords [cite: 38]

    def analyze_relevance(self, ngram, product_keywords):
        """Checks if the n-gram words exist in product metadata."""
        ngram_words = set(str(ngram).lower().split())
        if ngram_words & product_keywords: [cite: 43]
            return 'Relevant'
        return 'Irrelevant' [cite: 47]
