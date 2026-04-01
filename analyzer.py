import pandas as pd
import numpy as np
import re
from collections import defaultdict

def load_bulk_file(bulk_file_path):
    """Load and map Amazon headers with fuzzy matching to prevent 'Sales' errors."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    sp_df = pd.DataFrame()
    sb_df = pd.DataFrame()

    sp_sheet = next((s for s in sheet_names if 'Sponsored_Products' in s or s == 'SP Search Term Report'), None)
    sb_sheet = next((s for s in sheet_names if 'Sponsored_Brands' in s or s == 'SB Search Term Report'), None)

    def smart_rename(df):
        if df.empty: return df
        # Fuzzy mapping: Find columns containing these keywords
        mapping = {}
        for col in df.columns:
            c_lower = str(col).lower()
            if 'sales' in c_lower and 'advertised' not in c_lower and 'halo' not in c_lower:
                mapping[col] = 'Sales'
            elif 'orders' in c_lower:
                mapping[col] = 'Orders'
            elif 'acos' in c_lower:
                mapping[col] = 'ACOS'
            elif 'cpc' in c_lower or 'cost per click' in c_lower:
                mapping[col] = 'CPC'
            elif 'conversion rate' in c_lower:
                mapping[col] = 'Conversion Rate'
        return df.rename(columns=mapping)

    if sp_sheet:
        sp_df = smart_rename(pd.read_excel(excel_file, sp_sheet))
    if sb_sheet:
        sb_df = smart_rename(pd.read_excel(excel_file, sb_sheet))
    
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    """Combine reports and ensure the 'Sales' column exists."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Currency', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = []
    
    for df in [sp_df, sb_df]:
        if not df.empty:
            # Add missing columns with 0 to prevent KeyErrors
            for col in relevant_cols:
                if col not in df.columns:
                    df[col] = 0 if col != 'Customer Search Term' else 'Unknown'
            frames.append(df[relevant_cols])
    
    if not frames:
        raise ValueError("No data found in the uploaded sheets.")

    final_df = pd.concat(frames, ignore_index=True).fillna(0)
    for col in ['Spend', 'Sales', 'CPC']:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).round(2)
    return final_df

def get_exact_keyword_analysis(df):
    exact_df = df.copy()
    exact_df['ACOS'] = exact_df['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
    return exact_df.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    repeated_df = df[counts > 1].copy()
    repeated_df['ACOS'] = repeated_df['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
    return repeated_df.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def get_auto_to_manual_harvest(df):
    auto_df = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual_df = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual_terms = set(manual_df['Customer Search Term'].str.lower().unique())
    
    harvest_df = auto_df[(~auto_df['Customer Search Term'].str.lower().isin(manual_terms)) & (auto_df['Orders'] > 0)].copy()
    harvest_df['ACOS'] = harvest_df['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
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
                spend = float(row['Spend'])
                sales = float(row['Sales'])
                acos_val = (spend / sales * 100) if sales > 0 else 0
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(spend, 2),
                    'Sales': round(sales, 2),
                    'Clicks': row['Clicks'],
                    'Orders': row['Orders'],
                    'ACOS': f"{round(acos_val, 2)}%"
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
