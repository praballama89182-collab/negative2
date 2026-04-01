import streamlit as st
import pandas as pd
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis, get_exact_keyword_analysis

st.set_page_config(page_title="PPC Analyzer", layout="wide")

# Sidebar for N-Gram configuration
with st.sidebar:
    st.header("⚙️ Settings")
    ngram_sizes = st.multiselect("Select N-Grams:", [1, 2, 3], default=[1, 2, 3])

st.title("🚀 Amazon PPC Campaign & Keyword Analyzer")

uploaded_file = st.file_uploader("Upload Amazon Bulk File (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        sp_df, sb_df = load_bulk_file(uploaded_file)
        df = aggregate_data(sp_df, sb_df)

        # 1. Top Level Metrics
        st.header("📊 Account Overview (AED)")
        m1, m2, m3, m4 = st.columns(4)
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        total_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        
        m1.metric("Total Spend", f"{total_spend:,.2f}")
        m2.metric("Total Sales", f"{total_sales:,.2f}")
        m3.metric("Total Orders", int(df['Orders'].sum()))
        m4.metric("Total ACOS", f"{total_acos:.2f}%")

        # 2. Tabs for different views
        tab1, tab2 = st.tabs(["🎯 Exact Keywords per Campaign", "✂️ N-Gram Negation Tab"])

        with tab1:
            st.subheader("Performance by Full Search Term")
            st.write("Use this tab to see which exact keywords are driving high ACOS in specific campaigns.")
            exact_data = get_exact_keyword_analysis(df)
            st.dataframe(exact_data, use_container_width=True)

        with tab2:
            st.subheader("N-Gram Breakdown (Identify Wasted Spend)")
            st.write("Filter these results to find words that consistently spend without orders.")
            if ngram_sizes:
                cols = st.columns(len(ngram_sizes))
                for idx, size in enumerate(ngram_sizes):
                    with cols[idx]:
                        st.write(f"**{size}-Gram Analysis**")
                        res_df = perform_ngram_analysis(df, size)
                        st.dataframe(res_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
