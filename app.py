import streamlit as st
import pandas as pd
import plotly.express as px
from analyzer import (load_bulk_file, aggregate_data, perform_ngram_analysis, 
                      get_exact_keyword_analysis, get_repeated_keywords, get_auto_to_manual_harvest, get_brand_data)

st.set_page_config(page_title="AKOI PPC Analyzer", layout="wide")

with st.sidebar:
    st.header("⚙️ Settings")
    ngram_sizes = st.multiselect("Select N-Grams:", [1, 2, 3], default=[1, 2, 3])
    acos_limit = st.slider("Highlight ACOS above %:", 0.0, 200.0, 70.0, step=0.1)

st.title("🚀 Amazon PPC Multi-Brand Analyzer")

uploaded_file = st.file_uploader("Upload Search Term Report (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        sp_df, sb_df = load_bulk_file(uploaded_file)
        df = aggregate_data(sp_df, sb_df)

        # --- CURRENT OVERVIEW ---
        st.header("📊 Account Overview (AED)")
        m1, m2, m3, m4 = st.columns(4)
        t_spend, t_sales = float(df['Spend'].sum()), float(df['Sales'].sum())
        t_acos = (t_spend / t_sales * 100) if t_sales > 0 else 0
        
        m1.metric("Total Spend", f"{t_spend:,.2f}")
        m2.metric("Total Sales", f"{t_sales:,.2f}")
        m3.metric("Total Orders", int(df['Orders'].sum()))
        m4.metric("Total ACOS", f"{t_acos:.2f}%")

        # --- BRAND LEVEL CONTRIBUTION ---
        st.divider()
        st.header("🏷️ Brand Level Contribution")
        brand_df = get_brand_data(df)
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # Pie chart with light tones
            fig = px.pie(brand_df, values='Sales', names='Brand', 
                         title='Sales Contribution by Brand',
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("**Brand Performance Metrics**")
            # Format ACOS for display
            display_brand_df = brand_df.copy()
            display_brand_df['ACOS'] = display_brand_df['ACOS'].apply(lambda x: f"{x}%")
            st.table(display_brand_df)

        st.divider()
        t1, t2, t3, t4 = st.tabs(["🎯 Exact Keywords", "✂️ N-Gram Negation", "🔄 Keyword Repeat", "🚀 Harvesting"])

        with t1:
            st.dataframe(get_exact_keyword_analysis(df), use_container_width=True)

        with t2:
            if ngram_sizes:
                cols = st.columns(len(ngram_sizes))
                for idx, size in enumerate(ngram_sizes):
                    with cols[idx]:
                        st.write(f"**{size}-Gram Analysis**")
                        st.dataframe(perform_ngram_analysis(df, size).head(100), use_container_width=True)

        with t3:
            rep_df = get_repeated_keywords(df)
            def highlight_acos(row):
                try:
                    val = float(str(row.ACOS).replace('%', ''))
                    return ['background-color: #ffcccc' if val > acos_limit else '' for _ in row]
                except: return ['' for _ in row]
            if not rep_df.empty:
                st.dataframe(rep_df.style.apply(highlight_acos, axis=1), use_container_width=True)
            else: st.info("No repeated keywords found.")

        with t4:
            hv_df = get_auto_to_manual_harvest(df)
            if not hv_df.empty:
                st.dataframe(hv_df, use_container_width=True)
            else: st.info("No new converting terms found in Auto.")

    except Exception as e:
        st.error(f"Error: {e}")
