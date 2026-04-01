import streamlit as st
import pandas as pd
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis, get_exact_keyword_analysis, get_repeated_keywords

st.set_page_config(page_title="AKOI PPC Analyzer", layout="wide") [cite: 5]

with st.sidebar:
    st.header("⚙️ Settings") [cite: 5]
    ngram_sizes = st.multiselect("Select N-Grams:", [1, 2, 3], default=[1, 2, 3]) [cite: 5]
    acos_limit = st.slider("Highlight ACOS above %:", 0.0, 200.0, 70.0, step=0.1) [cite: 5]

st.title("🚀 Amazon PPC Campaign & Keyword Analyzer") [cite: 5]

uploaded_file = st.file_uploader("Upload Search Term Report (.xlsx)", type=["xlsx"]) [cite: 6]

if uploaded_file:
    try:
        sp_df, sb_df = load_bulk_file(uploaded_file) [cite: 6]
        df = aggregate_data(sp_df, sb_df) [cite: 6]

        # 1. Top Level Metrics [cite: 12]
        st.header("📊 Account Overview (AED)")
        m1, m2, m3, m4 = st.columns(4)
        t_spend = df['Spend'].sum()
        t_sales = df['Sales'].sum()
        t_acos = (t_spend / t_sales * 100) if t_sales > 0 else 0
        
        m1.metric("Total Spend", f"{t_spend:,.1f}")
        m2.metric("Total Sales", f"{t_sales:,.1f}")
        m3.metric("Total Orders", int(df['Orders'].sum()))
        m4.metric("Total ACOS", f"{t_acos:.1f}%")
        st.divider()

        # 2. Tabs [cite: 13]
        tab1, tab2, tab3 = st.tabs(["🎯 Exact Keywords", "✂️ N-Gram Negation", "🔄 Keyword Repeat"])

        with tab1:
            st.dataframe(get_exact_keyword_analysis(df), use_container_width=True)

        with tab2:
            if ngram_sizes:
                cols = st.columns(len(ngram_sizes))
                for idx, size in enumerate(ngram_sizes):
                    with cols[idx]:
                        st.write(f"**{size}-Gram Analysis**")
                        st.dataframe(perform_ngram_analysis(df, size), use_container_width=True)

        with tab3:
            repeat_df = get_repeated_keywords(df)
            
            def highlight_acos(row):
                # Convert string "75.4%" back to float 75.4 for comparison
                try:
                    val = float(str(row.ACOS).replace('%', ''))
                    return ['background-color: #ffcccc' if val > acos_limit else '' for _ in row]
                except:
                    return ['' for _ in row]

            if not repeat_df.empty:
                st.dataframe(repeat_df.style.apply(highlight_acos, axis=1), use_container_width=True)
            else:
                st.info("No repeated keywords found.")

    except Exception as e:
        st.error(f"Error: {e}")
