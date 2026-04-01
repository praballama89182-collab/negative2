import pandas as pd
import numpy as np
import re

def load_bulk_file(bulk_file_path):
    """Load and map Amazon-specific headers for AED performance."""
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
    """Standardize data for analysis."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = [df[relevant_cols] for df in [sp_df, sb_df] if not df.empty]
    return pd.concat(frames, ignore_index=True).fillna(0)

def get_exact_keyword_analysis(df):
    """Returns exact search terms per campaign, sorted by spend."""
    exact_df = df.copy()
    # Ensure Sales and Spend are rounded for the UI
    exact_df['Spend'] = exact_df['Spend'].round(2)
    exact_df['Sales'] = exact_df['Sales'].round(2)
    exact_df['ACOS'] = exact_df['ACOS'].round(2)
    return exact_df.sort_values('Spend', ascending=False).reset_index(drop=True)

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
    """Analyze n-grams while preserving 1:1 Campaign Name context."""
    res = []
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        for ng in ngrams:
            if not is_asin(ng):
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(row['Spend'], 2),
                    'Sales': round(row['Sales'], 2),
                    'Clicks': row['Clicks'],
                    'Orders': row['Orders'],
                    'ACOS': round(row['ACOS'], 2) if 'ACOS' in row else 0
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
