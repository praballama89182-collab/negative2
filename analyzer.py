import pandas as pd
import numpy as np
import re

# ... (Keep load_bulk_file, aggregate_data, get_exact_keyword_analysis, get_repeated_keywords)

def get_auto_to_manual_harvest(df):
    """
    Identifies search terms from Auto campaigns that are NOT present 
    in Manual campaigns. Filters for terms with at least 1 order.
    """
    # 1. Identify which campaigns are 'Auto' vs 'Manual' based on common naming conventions
    auto_df = df[df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    manual_df = df[~df['Campaign Name'].str.contains('Auto', case=False, na=False)].copy()
    
    # 2. Get unique list of terms already in manual campaigns
    manual_terms = set(manual_df['Customer Search Term'].str.lower().unique())
    
    # 3. Filter Auto terms that aren't in Manual and have at least 1 order
    harvest_df = auto_df[
        (~auto_df['Customer Search Term'].str.lower().isin(manual_terms)) & 
        (auto_df['Orders'] > 0)
    ].copy()
    
    # 4. Final Formatting
    harvest_df['Spend'] = harvest_df['Spend'].round(2)
    harvest_df['Sales'] = harvest_df['Sales'].round(2)
    harvest_df['ACOS'] = harvest_df['ACOS'].apply(lambda x: f"{round(x, 2)}%")
    
    return harvest_df.sort_values('Orders', ascending=False).reset_index(drop=True)

# ... (Keep is_asin and perform_ngram_analysis)
