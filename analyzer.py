import pandas as pd
import numpy as np
import re
from collections import defaultdict

def load_bulk_file(bulk_file_path):
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
        sp_df = pd.read_excel(excel_file, sp_sheet).rename(columns=column_mapping) [cite: 6]
    if sb_sheet:
        sb_df = pd.read_excel(excel_file, sb_sheet).rename(columns=column_mapping) [cite: 6]
    
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = []
    if not sp_df.empty: frames.append(sp_df[[c for c in relevant_cols if c in sp_df.columns]]) [cite: 6]
    if not sb_df.empty: frames.append(sb_df[[c for c in relevant_cols if c in sb_df.columns]]) [cite: 6]
    
    df = pd.concat(frames, ignore_index=True).fillna(0) [cite: 6]
    # Round metrics to 1 decimal place 
    for col in ['Spend', 'Sales', 'CPC']:
        df[col] = df[col].round(1)
    return df

def get_exact_keyword_analysis(df):
    exact_df = df.copy()
    # Format ACOS as percentage string 
    exact_df['ACOS'] = exact_df['ACOS'].apply(lambda x: f"{round(x, 1)}%")
    return exact_df.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique') [cite: 37]
    repeated_df = df[counts > 1].copy()
    # Format ACOS as percentage string 
    repeated_df['ACOS'] = repeated_df['ACOS'].apply(lambda x: f"{round(x, 1)}%")
    return repeated_df.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper())) [cite: 2]

def perform_ngram_analysis(df, n):
    res = []
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split() [cite: 2, 3]
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)] [cite: 3]
        for ng in ngrams:
            if not is_asin(ng):
                acos_val = (row['Spend'] / row['Sales'] * 100) if row['Sales'] > 0 else 0
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(row['Spend'], 1),
                    'Sales': round(row['Sales'], 1),
                    'Clicks': row['Clicks'],
                    'Orders': row['Orders'],
                    'ACOS': f"{round(acos_val, 1)}%" # Percentage format 
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
