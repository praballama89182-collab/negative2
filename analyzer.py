import pandas as pd
import numpy as np
import re

def load_bulk_file(bulk_file_path):
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    sp_df = pd.DataFrame()
    sb_df = pd.DataFrame()

    sp_sheet = next((s for s in sheet_names if 'Sponsored_Products' in s or s == 'SP Search Term Report'), None)
    sb_sheet = next((s for s in sheet_names if 'Sponsored_Brands' in s or s == 'SB Search Term Report'), None)

    def clean_and_rename(df):
        if df.empty: return df
        # Strip invisible spaces from column headers
        df.columns = df.columns.str.strip()
        
        mapping = {}
        for col in df.columns:
            c_low = col.lower()
            if 'sales' in c_low and 'advertised' not in c_low and 'brand halo' not in c_low:
                mapping[col] = 'Sales'
            elif 'orders' in c_low:
                mapping[col] = 'Orders'
            elif 'acos' in c_low:
                mapping[col] = 'ACOS'
            elif 'cpc' in c_low or 'cost per click' in c_low:
                mapping[col] = 'CPC'
        return df.rename(columns=mapping)

    if sp_sheet:
        sp_df = clean_and_rename(pd.read_excel(excel_file, sp_sheet))
    if sb_sheet:
        sb_df = clean_and_rename(pd.read_excel(excel_file, sb_sheet))
    
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Currency', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC']
    frames = []
    
    for df in [sp_df, sb_df]:
        if not df.empty:
            for col in relevant_cols:
                if col not in df.columns:
                    df[col] = 0 if col != 'Customer Search Term' else 'Unknown'
            frames.append(df[relevant_cols])
    
    if not frames:
        raise ValueError("No valid PPC data detected.")

    final_df = pd.concat(frames, ignore_index=True).fillna(0)
    
    # Force everything to be a numeric Series to fix the 'arg' error
    for col in ['Spend', 'Sales', 'Orders', 'ACOS', 'CPC', 'Impressions', 'Clicks']:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
    
    return final_df

def format_acos(val):
    """Detects if ACOS is decimal (0.05) or percentage (5.0) and formats correctly."""
    try:
        f_val = float(val)
        # If it's a small decimal (like 0.05 from your raw file), multiply by 100
        if 0 < f_val < 1.0:
            return f"{round(f_val * 100, 2)}%"
        return f"{round(f_val, 2)}%"
    except:
        return "0.0%"

def get_exact_keyword_analysis(df):
    res = df.copy()
    res['ACOS'] = res['ACOS'].apply(format_acos)
    return res.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    rep = df[counts > 1].copy()
    rep['ACOS'] = rep['ACOS'].apply(format_acos)
    return rep.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def get_auto_to_manual_harvest(df):
    auto = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    m_terms = set(manual['Customer Search Term'].str.lower().unique())
    
    harvest = auto[(~auto['Customer Search Term'].str.lower().isin(m_terms)) & (auto['Orders'] > 0)].copy()
    harvest['ACOS'] = harvest['ACOS'].apply(format_acos)
    return harvest.sort_values('Orders', ascending=False).reset_index(drop=True)

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(df, n):
    res = []
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        for ng in ngrams:
            if not is_asin(ng):
                acos_calc = (row['Spend'] / row['Sales'] * 100) if row['Sales'] > 0 else 0
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(row['Spend'], 2),
                    'Sales': round(row['Sales'], 2),
                    'Clicks': int(row['Clicks']),
                    'Orders': int(row['Orders']),
                    'ACOS': f"{round(acos_calc, 2)}%"
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
