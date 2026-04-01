import requests
import pandas as pd
from datetime import datetime

class KeepaRelevanceAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.keepa.com/product"
        self.product_cache = {}

    def fetch_product_data(self, asin):
        if asin in self.product_cache:
            return self.product_cache[asin]
        
        params = {'key': self.api_key, 'asin': asin, 'domain': 1}
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data and 'products' in data and data['products']:
                product = data['products'][0]
                self.product_cache[asin] = product
                return product
        except Exception as e:
            print(f"Error fetching ASIN {asin}: {e}")
        return None

    def extract_keywords(self, product_data):
        keywords = set()
        if not product_data: return keywords
        
        for field in ['title', 'brand']:
            if field in product_data:
                keywords.update(str(product_data[field]).lower().split())
        
        if 'categoryTree' in product_data:
            for cat in product_data['categoryTree']:
                keywords.update(str(cat.get('name', '')).lower().split())
        return keywords

    def analyze_relevance(self, ngram, product_keywords):
        ngram_words = set(str(ngram).lower().split())
        if ngram_words & product_keywords:
            return 'Relevant'
        return 'Irrelevant'
