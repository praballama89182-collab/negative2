import streamlit as st
import pandas as pd
import io
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis

st.set_page_config(page_title="PPC Analyzer", layout="wide")

st.title("🚀 Amazon PPC Negative Keyword Analyzer")

uploaded_file = st.file_uploader("Upload Amazon Bulk File (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        sp_df, sb_df = load_bulk_file(uploaded_file)
        aggregated_df = aggregate_data(sp_df, sb_df)

        # --- OVERVIEW DASHBOARD ---
        st.header("📊 Account Overview")
        m1, m2, m3, m4 = st.columns(4)
        
        total_spend = aggregated_df['Spend'].sum()
        total_sales = aggregated_df['Sales'].sum()
        total_orders = aggregated_df['Orders'].sum()
        total_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        
        m1.metric("Total Spend", f"{total_spend:,.2f} AED")
        m2.metric("Total Sales", f"{total_sales:,.2f} AED")
        m3.metric("Total Orders", int(total_orders))
        m4.metric("Total ACOS", f"{total_acos:.2f}%")
        st.divider()

        # --- N-GRAM ANALYSIS ---
        ngram_sizes = [1, 2, 3]
        results = {size: perform_ngram_analysis(aggregated_df, size) for size in ngram_sizes}

        cols = st.columns(3)
        for idx, size in enumerate(ngram_sizes):
            with cols[idx]:
                st.subheader(f"{size}-Grams")
                st.dataframe(results[size].head(50), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
