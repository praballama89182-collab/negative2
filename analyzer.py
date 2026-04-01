import pandas as pd
import numpy as np
from collections import defaultdict
import re

def load_bulk_file(bulk_file_path):
    """Load and parse the bulk file, handling specific Amazon headers and sheet names."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    column_mapping = {
        '7 Day Total Sales ': 'Sales',
        '7 Day Total Orders (#)': 'Orders',
        'Total Advertising Cost of Sales (ACOS) ': 'ACOS',
        'Cost Per Click (CPC)': 'CPC',
        '7 Day Conversion Rate': 'Conversion Rate'
    }

    sp_df = pd.DataFrame()
    sb_df = pd.DataFrame()

    sp_sheet = next((s for s in sheet_names if 'Sponsored_Products' in s or s == 'SP Search Term Report'), None)
    sb_sheet = next((s for s in sheet_names if 'Sponsored_Brands' in s or s == 'SB Search Term Report'), None)

    if sp_sheet:
        sp_df = pd.read_excel(excel_file, sp_sheet).rename(columns=column_mapping)
    if sb_sheet:
        sb_df = pd.read_excel(excel_file, sb_sheet).rename(columns=column_mapping)
    
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    """Aggregate data while keeping Campaign Name."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    
    frames = []
    if not sp_df.empty: 
        frames.append(sp_df[[c for c in relevant_cols if c in sp_df.columns]])
    if not sb_df.empty: 
        frames.append(sb_df[[c for c in relevant_cols if c in sb_df.columns]])
    
    return pd.concat(frames, ignore_index=True).fillna(0)

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
    """Perform n-gram analysis including Campaign Name mapping."""
    ngram_data = defaultdict(lambda: {
        'freq': 0, 'impressions': 0, 'clicks': 0, 'spend': 0, 
        'sales': 0, 'orders': 0, 'campaigns': set()
    })
    
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        
        for ng in ngrams:
            if not is_asin(ng):
                ngram_data[ng]['freq'] += 1
                ngram_data[ng]['impressions'] += row['Impressions']
                ngram_data[ng]['clicks'] += row['Clicks']
                ngram_data[ng]['spend'] += row['Spend']
                ngram_data[ng]['sales'] += row['Sales']
                ngram_data[ng]['orders'] += row['Orders']
                if 'Campaign Name' in row and row['Campaign Name'] != 0:
                    ngram_data[ng]['campaigns'].add(str(row['Campaign Name']))
    
    res = []
    for term, m in ngram_data.items():
        res.append({
            'Term': term,
            'Campaigns': ", ".join(list(m['campaigns'])),
            'Frequency': m['freq'], 
            'Spend': round(m['spend'], 2),
            'Orders': m['orders'], 
            'Clicks': m['clicks'],
            'ACOS': round((m['spend']/m['sales']*100), 2) if m['sales'] > 0 else 0
        })
    return pd.DataFrame(res).sort_values('Spend', ascending=False)
