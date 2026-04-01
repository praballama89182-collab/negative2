import pandas as pd
import numpy as np
import re

def load_bulk_file(bulk_file_path):
    """Load and map UAE-specific headers with trailing space handling."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    # Specific mapping for UAE Search Term Report
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
    """Combine data and force numeric Series types to prevent 'arg' errors."""
    relevant_cols = ['Customer Search Term', 'Campaign Name', 'Spend', 'Sales', 'Orders', 'ACOS', 'Targeting']
    frames = []
    for df in [sp_df, sb_df]:
        if not df.empty:
            for col in relevant_cols:
                if col not in df.columns:
                    df[col] = 0
            frames.append(df[relevant_cols])
    
    final_df = pd.concat(frames, ignore_index=True).fillna(0)
    
    # Force metrics to numeric to ensure they are 1-D arrays
    for col in ['Spend', 'Sales', 'Orders', 'ACOS']:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
    
    return final_df

def get_brand_and_asin_data(df):
    """Maps campaign prefixes and ASINs to the 6 specific Brand Names."""
    def map_brand(campaign):
        c = str(campaign).upper()
        if c.startswith('PC'): return 'Paris Collection'
        if c.startswith('JPD'): return 'JPD'
        if c.startswith('CL'): return 'Creation Lamis'
        if c.startswith('DC'): return 'Dorall Collection'
        if c.startswith('CPT'): return 'CPT'
        if c.startswith('MA'): return 'Maison'
        return 'Other'

    brand_df = df.copy()
    brand_df['Brand'] = brand_df['Campaign Name'].apply(map_brand)
    
    # Brand Level Summary
    brand_summary = brand_df.groupby('Brand').agg({'Sales': 'sum', 'Spend': 'sum', 'Orders': 'sum'}).reset_index()
    brand_summary['ACOS'] = (brand_summary['Spend'] / brand_summary['Sales'] * 100).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    brand_summary['Sales'] = brand_summary['Sales'].round(2)
    brand_summary['Spend'] = brand_summary['Spend'].round(2)
    
    # Filter for your 6 brands
    main_brands = ['Paris Collection', 'JPD', 'Creation Lamis', 'Dorall Collection', 'CPT', 'Maison']
    brand_summary = brand_summary[brand_summary['Brand'].isin(main_brands)].sort_values('Sales', ascending=False)

    # ASIN Mapping (Targeting that looks like an ASIN)
    asin_data = brand_df[brand_df['Targeting'].str.match(r'^B[A-Z0-9]{9}$', na=False)].copy()
    asin_summary = asin_data.groupby(['Brand', 'Targeting']).agg({'Sales': 'sum', 'Spend': 'sum', 'Orders': 'sum'}).reset_index()
    asin_summary['ACOS'] = (asin_summary['Spend'] / asin_summary['Sales'] * 100).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    
    return brand_summary, asin_summary

def get_exact_keyword_analysis(df):
    res = df.copy()
    res['ACOS'] = res['ACOS'].apply(lambda x: f"{round(float(x) * 100 if 0 < float(x) < 1 else float(x), 2)}%")
    return res.sort_values('Spend', ascending=False).reset_index(drop=True)

def get_repeated_keywords(df):
    counts = df.groupby('Customer Search Term')['Campaign Name'].transform('nunique')
    rep = df[counts > 1].copy()
    rep['ACOS'] = rep['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
    return rep.sort_values(['Customer Search Term', 'Spend'], ascending=[True, False]).reset_index(drop=True)

def get_auto_to_manual_harvest(df):
    auto = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    m_terms = set(manual['Customer Search Term'].str.lower().unique())
    harvest = auto[(~auto['Customer Search Term'].str.lower().isin(m_terms)) & (auto['Orders'] > 0)].copy()
    harvest['ACOS'] = harvest['ACOS'].apply(lambda x: f"{round(float(x), 2)}%")
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
                spend, sales = float(row['Spend']), float(row['Sales'])
                acos_calc = (spend / sales * 100) if sales > 0 else 0
                res.append({
                    'Term': ng,
                    'Campaign Name': row['Campaign Name'],
                    'Spend': round(spend, 2),
                    'Sales': round(sales, 2),
                    'Orders': int(row['Orders']),
                    'ACOS': f"{round(acos_calc, 2)}%"
                })
    return pd.DataFrame(res).sort_values('Spend', ascending=False).reset_index(drop=True)
