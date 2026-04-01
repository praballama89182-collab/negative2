import pandas as pd
import numpy as np
from collections import defaultdict
import re

def load_bulk_file(bulk_file_path):
    excel_file = pd.ExcelFile(bulk_file_path)
    sp_df = pd.read_excel(excel_file, 'SP Search Term Report')
    sb_df = pd.read_excel(excel_file, 'SB Search Term Report')
    return sp_df, sb_df

def aggregate_data(sp_df, sb_df):
    relevant_cols = ['Customer Search Term', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'ACOS', 'CPC', 'Conversion Rate']
    combined_df = pd.concat([sp_df[relevant_cols], sb_df[relevant_cols]], ignore_index=True).fillna(0)
    
    aggregated = combined_df.groupby('Customer Search Term').agg({
        'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
    }).reset_index()
    
    aggregated['ACOS'] = np.where(aggregated['Sales'] > 0, (aggregated['Spend'] / aggregated['Sales'] * 100), 0)
    aggregated['CPC'] = np.where(aggregated['Clicks'] > 0, aggregated['Spend'] / aggregated['Clicks'], 0)
    return aggregated

def is_asin(term):
    return bool(re.match(r'^B[A-Z0-9]{9}$', str(term).upper()))

def perform_ngram_analysis(aggregated_df, n):
    ngram_data = defaultdict(lambda: {'freq': 0, 'impressions': 0, 'clicks': 0, 'spend': 0, 'sales': 0, 'orders': 0})
    for _, row in aggregated_df.iterrows():
        words = str(row['Customer Search Term']).lower().split()
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        for ng in ngrams:
            if not is_asin(ng):
                ngram_data[ng]['freq'] += 1
                for metric in ['impressions', 'clicks', 'spend', 'sales', 'orders']:
                    ngram_data[ng][metric] += row[metric.capitalize()]
    
    res = []
    for term, m in ngram_data.items():
        res.append({
            'Term': term, 'Frequency': m['freq'], 'Spend': round(m['spend'], 2),
            'Orders': m['orders'], 'Clicks': m['clicks'],
            'ACOS': round((m['spend']/m['sales']*100), 2) if m['sales'] > 0 else 0
        })
    return pd.DataFrame(res).sort_values('Spend', ascending=False)
