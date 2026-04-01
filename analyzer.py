import pandas as pd
import numpy as np
from collections import defaultdict
import re

def load_bulk_file(bulk_file_path):
    """Load and parse the bulk file, extracting SP and SB search term reports."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sp_df = pd.read_excel(excel_file, 'SP Search Term Report')
    sb_df = pd.read_excel(excel_file, 'SB Search Term Report')
    return sp_df, sb_df [cite: 122]

def aggregate_data(sp_df, sb_df):
    """Aggregate SP and SB search term data."""
    relevant_cols = ['Customer Search Term', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC', 'Conversion Rate']
    combined_df = pd.concat([sp_df[relevant_cols], sb_df[relevant_cols]], ignore_index=True).fillna(0)
    
    aggregated = combined_df.groupby('Customer Search Term').agg({
        'Impressions': 'sum', 
        'Clicks': 'sum', 
        'Spend': 'sum', 
        'Sales': 'sum', 
        'Orders': 'sum'
    }).reset_index() [cite: 122, 123]
    
    aggregated['ACOS'] = np.where(aggregated['Sales'] > 0, (aggregated['Spend'] / aggregated['Sales'] * 100), 0)
    aggregated['CPC'] = np.where(aggregated['Clicks'] > 0, aggregated['Spend'] / aggregated['Clicks'], 0)
    return aggregated [cite: 123]

def is_asin(term):
    """Check if a term is an ASIN."""
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper())) [cite: 123]

def perform_ngram_analysis(aggregated_df, n):
    """Perform n-gram analysis on the aggregated data."""
    ngram_data = defaultdict(lambda: {'freq': 0, 'impressions': 0, 'clicks': 0, 'spend': 0, 'sales': 0, 'orders': 0})
    
    for _, row in aggregated_df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        
        for ng in ngrams:
            if not is_asin(ng):
                ngram_data[ng]['freq'] += 1
                ngram_data[ng]['impressions'] += row['Impressions']
                ngram_data[ng]['clicks'] += row['Clicks']
                ngram_data[ng]['spend'] += row['Spend']
                ngram_data[ng]['sales'] += row['Sales']
                ngram_data[ng]['orders'] += row['Orders'] [cite: 124]
    
    res = []
    for term, m in ngram_data.items():
        res.append({
            'Term': term, 
            'Frequency': m['freq'], 
            'Spend': round(m['spend'], 2),
            'Orders': m['orders'], 
            'Clicks': m['clicks'],
            'ACOS': round((m['spend']/m['sales']*100), 2) if m['sales'] > 0 else 0
        }) [cite: 125]
    
    return pd.DataFrame(res).sort_values('Spend', ascending=False) [cite: 125]
