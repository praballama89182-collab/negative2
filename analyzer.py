import requests
import pandas as pd
from datetime import datetime

class KeepaRelevanceAnalyzer:
    def __init__(self, api_key):
        """Initialize with Keepa API key."""
        self.api_key = api_key
        self.base_url = "https://api.keepa.com/product"
        self.product_cache = {}

    def fetch_product_data(self, asin):
        """Fetch product data from Keepa API."""
        if asin in self.product_cache:
            return self.product_cache[asin]
        
        params = {'key': self.api_key, 'asin': asin, 'domain': 1}
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, dict) and 'products' in data and data['products']:
                product = data['products'][0]
                self.product_cache[asin] = product
                return product
            return None
        except Exception as e:
            print(f"Error fetching ASIN {asin}: {e}")
            return None

    def extract_keywords(self, product_data):
        """Extract relevant keywords from product data."""
        keywords = set()
        if not product_data:
            return keywords
        
        for field in ['title', 'brand']:
            if field in product_data:
                val = str(product_data[field]).lower().split()
                keywords.update(val)
        
        if 'categoryTree' in product_data:
            for cat in product_data['categoryTree']:
                if isinstance(cat, dict) and 'name' in cat:
                    cat_words = str(cat.get('name', '')).lower().split()
                    keywords.update(cat_words)
        return keywords

    def analyze_relevance(self, ngram, product_keywords):
        """Checks if the n-gram words exist in product metadata."""
        ngram_words = set(str(ngram).lower().split())
        if ngram_words & product_keywords:
            return 'Relevant'
        return 'Irrelevant'
