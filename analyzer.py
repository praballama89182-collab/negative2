import pandas as pd
import numpy as np
from collections import defaultdict
import re

def load_bulk_file(bulk_file_path):
    """Load and parse the bulk file, handling missing sheets and specific Amazon headers."""
    excel_file = pd.ExcelFile(bulk_file_path)
    sheet_names = excel_file.sheet_names
    
    # Mapping for your specific file headers to standard names
    column_mapping = {
        '7 Day Total Sales ': 'Sales',
        '7 Day Total Orders (#)': 'Orders',
        'Total Advertising Cost of Sales (ACOS) ': 'ACOS',
        'Cost Per Click (CPC)': 'CPC',
        '7 Day Conversion Rate': 'Conversion Rate'
    }

    sp_df = pd.DataFrame()
    sb_df = pd.DataFrame()

    # Look for the sheet names the user actually has or the standard ones
    sp_sheet = next((s for s in sheet_names if 'Sponsored_Products' in s or s == 'SP Search Term Report'), None)
    sb_sheet = next((s for s in sheet_names if 'Sponsored_Brands' in s or s == 'SB Search Term Report'), None)

    if sp_sheet:
        sp_df = pd.read_excel(excel_file, sp_sheet).rename(columns=column_mapping)
    if sb_sheet:
        sb_df = pd.read_excel(excel_file, sb_sheet).rename(columns=column_mapping)
    
    if sp_df.empty and sb_df.empty:
        raise ValueError("No valid PPC data sheets found in the file.")
        
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    """Aggregate data while checking for existence of dataframes."""
    relevant_cols = ['Customer Search Term', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC', 'Conversion Rate']
    
    frames = []
    if not sp_df.empty: frames.append(sp_df[[c for c in relevant_cols if c in sp_df.columns]])
    if not sb_df.empty: frames.append(sb_df[[c for c in relevant_cols if c in sb_df.columns]])
    
    combined_df = pd.concat(frames, ignore_index=True).fillna(0)
    
    aggregated = combined_df.groupby('Customer Search Term').agg({
        'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
    }).reset_index()
    
    aggregated['ACOS'] = np.where(aggregated['Sales'] > 0, (aggregated['Spend'] / aggregated['Sales'] * 100), 0)
    aggregated['CPC'] = np.where(aggregated['Clicks'] > 0, aggregated['Spend'] / aggregated['Clicks'], 0)
    return aggregated

# Rest of the functions (is_asin, perform_ngram_analysis) remain the same as your previous analyzer.py
