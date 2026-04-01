import pandas as pd
import numpy as np
import re
from collections import defaultdict

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
    """Standardize data and combine SP and SB reports with 2-decimal rounding."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = []
    if not sp_df.empty: frames.append(sp_df[[c for c in relevant_cols if c in sp_df.columns]])
    if not sb_df.empty: frames.append(sb_df[[c for c in relevant_cols if c in sb_df.columns]])
    
    df = pd.concat(frames, ignore_index=True).fillna(0)
    for col in ['Spend', 'Sales', 'CPC']:
        df[col] = df[col].round(2)
    return df

def get_exact_keyword_analysis(df):
    """Returns exact search terms sorted by spend with 2-decimal percentage ACOS."""
    exact_df = df.copy()
    exact_df['ACOS'] = exact_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    return exact_df.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    """Identifies keywords in >1 campaign with 2-decimal rounding for all metrics."""
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    repeated_df = df[counts > 1].copy()
    # Explicitly round currency for the repeat tab
    repeated_df['Spend'] = repeated_df['Spend'].round(2)
    repeated_df['Sales'] = repeated_df['Sales'].round(2)
    repeated_df['ACOS'] = repeated_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    return repeated_df.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def is_asin(term):
    """Filter out Amazon ASINs from n-gram results."""
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
    """Breaks down search terms into n-grams with 2-decimal rounding."""
    res = []
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        for ng in ngrams:
            if not is_asin(ng):
                acos_val = (row['Spend'] / row['Sales'] * 100) if row['Sales'] > 0 else 0
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(row['Spend'], 2),
                    'Sales': round(row['Sales'], 2),
                    'Clicks': row['Clicks'],
                    'Orders': row['Orders'],
                    'ACOS': f"{round(acos_val, 2)}%"
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
