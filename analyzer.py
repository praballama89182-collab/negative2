import pandas as pd
import numpy as np
import re
from collections import defaultdict

def load_bulk_file(bulk_file_path):
    """Load and map Amazon headers for both UAE (7-day) and India (14-day) reports."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    # Comprehensive mapping for global Amazon Search Term Reports
    column_mapping = {
        # Sales Mapping
        '7 Day Total Sales ': 'Sales',
        '14 Day Total Sales (₹)': 'Sales',
        # Orders Mapping
        '7 Day Total Orders (#)': 'Orders',
        '14 Day Total Orders (#)': 'Orders',
        # ACOS Mapping
        'Total Advertising Cost of Sales (ACOS) ': 'ACOS',
        # CPC Mapping
        'Cost Per Click (CPC)': 'CPC',
        # Conversion Rate Mapping
        '7 Day Conversion Rate': 'Conversion Rate',
        '14 Day Conversion Rate': 'Conversion Rate'
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
    """Combine reports with rounding to 2 decimal places."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Currency', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = []
    
    for df in [sp_df, sb_df]:
        if not df.empty:
            # Ensure missing columns (like Currency) don't crash the concat
            existing_cols = [c for c in relevant_cols if c in df.columns]
            frames.append(df[existing_cols])
    
    final_df = pd.concat(frames, ignore_index=True).fillna(0)
    for col in ['Spend', 'Sales', 'CPC']:
        if col in final_df.columns:
            final_df[col] = final_df[col].round(2)
    return final_df

def get_exact_keyword_analysis(df):
    exact_df = df.copy()
    exact_df['ACOS'] = exact_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    return exact_df.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    repeated_df = df[counts > 1].copy()
    repeated_df['ACOS'] = repeated_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    return repeated_df.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def get_auto_to_manual_harvest(df):
    auto_df = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual_df = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual_terms = set(manual_df['Customer Search Term'].str.lower().unique())
    
    harvest_df = auto_df[
        (~auto_df['Customer Search Term'].str.lower().isin(manual_terms)) & (auto_df['Orders'] > 0)
    ].copy()
    harvest_df['ACOS'] = harvest_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    return harvest_df.sort_values('Orders', ascending=False).reset_index(drop=True)

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
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
