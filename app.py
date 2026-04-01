import streamlit as st
import pandas as pd
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis, get_exact_keyword_analysis, get_repeated_keywords

# Page Configuration [cite: 5]
st.set_page_config(page_title="AKOI PPC Analyzer", layout="wide")

# Sidebar for Filters
with st.sidebar:
    st.header("⚙️ Settings")
    ngram_sizes = st.multiselect("Select N-Grams to analyze:", [1, 2, 3], default=[1, 2, 3])
    # Slider to control the red highlighting threshold
    acos_limit = st.slider("Highlight ACOS (Repeat Tab) above %:", 0, 200, 70)

st.title("🚀 Amazon PPC Campaign & Keyword Analyzer")

uploaded_file = st.file_uploader("Upload Sponsored Products Search Term Report (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Load and Combine Data
        sp_df, sb_df = load_bulk_file(uploaded_file)
        df = aggregate_data(sp_df, sb_df)

        # 1. TOP OVERVIEW DASHBOARD 
        st.header("📊 Account Performance Overview (AED)")
        m1, m2, m3, m4 = st.columns(4)
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        total_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        
        m1.metric("Total Spend", f"{total_spend:,.2f}")
        m2.metric("Total Sales", f"{total_sales:,.2f}")
        m3.metric("Total Orders", int(df['Orders'].sum()))
        m4.metric("Total ACOS", f"{total_acos:.2f}%")
        st.divider()

        # 2. TABBED NAVIGATION [cite: 12]
        tab1, tab2, tab3 = st.tabs(["🎯 Exact Keywords", "✂️ N-Gram Negation", "🔄 Keyword Repeat"])

        with tab1:
            st.subheader("Performance by Full Search Term")
            exact_data = get_exact_keyword_analysis(df)
            st.dataframe(exact_data, use_container_width=True)

        with tab2:
            st.subheader("N-Gram Breakdown (Identify Wasted Spend)")
            if ngram_sizes:
                cols = st.columns(len(ngram_sizes))
                for idx, size in enumerate(ngram_sizes):
                    with cols[idx]:
                        st.write(f"**{size}-Gram Analysis**")
                        res_df = perform_ngram_analysis(df, size)
                        st.dataframe(res_df.head(100), use_container_width=True)

        with tab3:
            st.subheader("Duplicate Keywords Across Campaigns")
            repeat_df = get_repeated_keywords(df)
            
            # High ACOS Row Styling Function
            def highlight_acos(row):
                # Apply light red background if ACOS exceeds your slider setting
                return ['background-color: #ffcccc' if row.ACOS > acos_limit else '' for _ in row]

            if not repeat_df.empty:
                styled_df = repeat_df.style.apply(highlight_acos, axis=1)
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("No repeated keywords found across different campaigns.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
