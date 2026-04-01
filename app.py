import streamlit as st
import pandas as pd
from analyzer import (load_bulk_file, aggregate_data, perform_ngram_analysis, 
                      get_exact_keyword_analysis, get_repeated_keywords, get_auto_to_manual_harvest)

st.set_page_config(page_title="AKOI Global PPC Analyzer", layout="wide")

with st.sidebar:
    st.header("⚙️ Settings")
    ngram_sizes = st.multiselect("Select N-Grams:", [1, 2, 3], default=[1, 2, 3])
    acos_limit = st.slider("Highlight ACOS (Repeat Tab) above %:", 0.0, 200.0, 70.0, step=0.01)

st.title("🚀 Amazon Global PPC Campaign & Keyword Analyzer")

uploaded_file = st.file_uploader("Upload Search Term Report (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        sp_df, sb_df = load_bulk_file(uploaded_file)
        df = aggregate_data(sp_df, sb_df)

        # Detect Currency from the file
        currency = df['Currency'].iloc[0] if 'Currency' in df.columns and not df.empty else "Currency"

        # TOP OVERVIEW DASHBOARD
        st.header(f"📊 Account Performance Overview ({currency})")
        m1, m2, m3, m4 = st.columns(4)
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        total_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        
        m1.metric("Total Spend", f"{total_spend:,.2f} {currency}")
        m2.metric("Total Sales", f"{total_sales:,.2f} {currency}")
        m3.metric("Total Orders", int(df['Orders'].sum()))
        m4.metric("Total ACOS", f"{total_acos:.2f}%")
        st.divider()

        # TABBED NAVIGATION
        t1, t2, t3, t4 = st.tabs(["🎯 Exact Keywords", "✂️ N-Gram Negation", "🔄 Keyword Repeat", "🚀 Harvesting Tab"])

        with t1:
            st.dataframe(get_exact_keyword_analysis(df), use_container_width=True)

        with t2:
            if ngram_sizes:
                cols = st.columns(len(ngram_sizes))
                for idx, size in enumerate(ngram_sizes):
                    with cols[idx]:
                        st.write(f"**{size}-Gram Analysis**")
                        res_df = perform_ngram_analysis(df, size)
                        st.dataframe(res_df.head(100), use_container_width=True)

        with t3:
            repeat_df = get_repeated_keywords(df)
            def highlight_acos(row):
                try:
                    val = float(str(row.ACOS).replace('%', ''))
                    return ['background-color: #ffcccc' if val > acos_limit else '' for _ in row]
                except: return ['' for _ in row]
            if not repeat_df.empty:
                st.dataframe(repeat_df.style.apply(highlight_acos, axis=1), use_container_width=True)
            else:
                st.info("No repeated keywords found.")

        with t4:
            st.subheader("Auto-to-Manual Harvesting")
            harvest_df = get_auto_to_manual_harvest(df)
            if not harvest_df.empty:
                st.dataframe(harvest_df, use_container_width=True)
                st.success(f"Found {len(harvest_df)} new high-potential keywords!")
            else:
                st.info("No new converting terms found in Auto campaigns.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
