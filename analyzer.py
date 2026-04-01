import pandas as pd
import numpy as np
import re

def load_bulk_file(bulk_file_path):
    """Load and map UAE-specific headers with trailing space handling."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    column_mapping = {
        '7 Day Total Sales ': 'Sales',
        '7 Day Total Orders (#)': 'Orders',
        'Total Advertising Cost of Sales (ACOS) ': 'ACOS',
        'Cost Per Click (CPC)': 'CPC'
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
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Spend', 'Sales', 'Orders', 'ACOS', 'Clicks']
    frames = []
    for df in [sp_df, sb_df]:
        if not df.empty:
            for col in relevant_cols:
                if col not in df.columns:
                    df[col] = 0 if col != 'Customer Search Term' else 'Unknown'
            frames.append(df[relevant_cols])
    
    final_df = pd.concat(frames, ignore_index=True).fillna(0)
    for col in ['Spend', 'Sales', 'Orders', 'ACOS']:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
    
    return final_df

def format_term(term):
    """
    Fixed Regex: Uses A-Za-z0-9 to avoid 'bad character range' error.
    Forces ASINs starting with B to UPPERCASE.
    """
    t_str = str(term).strip()
    # Corrected range: A-Z followed by a-z
    if re.match(r'^[Bb][A-Za-z0-9]{9}$', t_str):
        return t_str.upper()
    return t_str

def get_exact_keyword_analysis(df):
    res = df.copy()
    res['Customer Search Term'] = res['Customer Search Term'].apply(format_term)
    res['ACOS'] = res['ACOS'].apply(lambda x: f"{round(float(x) * 100 if 0 < float(x) < 1 else float(x), 2)}%")
    return res.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    rep = df[counts > 1].copy()
    rep['Customer Search Term'] = rep['Customer Search Term'].apply(format_term)
    rep['ACOS'] = rep['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
    return rep.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def get_auto_to_manual_harvest(df):
    auto = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    m_terms = set(manual['Customer Search Term'].str.lower().unique())
    harvest = auto[(~auto['Customer Search Term'].str.lower().isin(m_terms)) & (auto['Orders'] > 0)].copy()
    
    harvest['Customer Search Term'] = harvest['Customer Search Term'].apply(format_term)
    harvest['ACOS'] = harvest['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
    return harvest.sort_values('Orders', ascending=False).reset_index(drop=True)

def perform_ngram_analysis(df, n):
    res = []
    for _, row in df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        for ng in ngrams:
            formatted_ng = format_term(ng)
            spend, sales = float(row['Spend']), float(row['Sales'])
            acos_calc = (spend / sales * 100) if sales > 0 else 0
            res.append({
                'Term': formatted_ng,
                'Campaign Name': row['Campaign Name'],
                'Spend': round(spend, 2),
                'Sales': round(sales, 2),
                'Orders': int(row['Orders']),
                'ACOS': f"{round(acos_calc, 2)}%"
            })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
