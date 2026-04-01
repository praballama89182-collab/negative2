import pandas as pd
import numpy as np
import re

def load_bulk_file(bulk_file_path):
    """Load the file and map your specific Amazon column names."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    # Mapping your specific headers to names the app understands
    column_mapping = {
        '7 Day Total Sales ': 'Sales',
        '7 Day Total Orders (#)': 'Orders',
        'Total Advertising Cost of Sales (ACOS) ': 'ACOS',
        'Cost Per Click (CPC)': 'CPC',
        '7 Day Conversion Rate': 'Conversion Rate'
    }

    sp_df = pd.DataFrame()
    sb_df = pd.DataFrame()

    # Detect your Sponsored Products sheet
    sp_sheet = next((s for s in sheet_names if 'Sponsored_Products' in s or s == 'SP Search Term Report'), None)
    sb_sheet = next((s for s in sheet_names if 'Sponsored_Brands' in s or s == 'SB Search Term Report'), None)

    if sp_sheet:
        sp_df = pd.read_excel(excel_file, sp_sheet).rename(columns=column_mapping)
    if sb_sheet:
        sb_df = pd.read_excel(excel_file, sb_sheet).rename(columns=column_mapping)
    
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    """Combine data while keeping all rows for detailed campaign analysis."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    
    frames = []
    if not sp_df.empty: 
        frames.append(sp_df[[c for c in relevant_cols if c in sp_df.columns]])
    if not sb_df.empty: 
        frames.append(sb_df[[c for c in relevant_cols if c in sb_df.columns]])
    
    return pd.concat(frames, ignore_index=True).fillna(0)

def is_asin(term):
    """Exclude ASINs from the keyword list."""
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
    """Analyze every search term and keep the campaign context."""
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
                    'Sales': round(row['Sales'], 2), # Fixed: Now correctly maps from your file
                    'Clicks': row['Clicks'],
                    'Orders': row['Orders'],
                    'ACOS': round(row['ACOS'], 2) if 'ACOS' in row else 0,
                    'Search Term': row['Customer Search Term']
                })
    
    # Sort by Spend (Highest first) to find wasted budget quickly
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
