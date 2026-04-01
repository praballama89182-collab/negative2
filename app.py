import streamlit as st  # Ensure this is the first line
import pandas as pd
import io
import os
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis
from keepa_relevance_analyzer import KeepaRelevanceAnalyzer

# Page configuration
st.set_page_config(page_title="PPC Negative Keyword Analyzer", layout="wide")

st.title("🚀 Amazon PPC Negative Keyword Analyzer")
st.markdown("""
Upload your **Amazon Bulk File** to identify wasted ad spend through n-gram analysis. 
Optionally, connect to **Keepa** to automatically flag terms that do not match your product metadata.
""")

# Sidebar for Configuration
with st.sidebar:
    st.header("1. Analysis Settings")
    # This is the line where your error occurred (line 21)
    ngram_sizes = st.multiselect("Select N-Grams to analyze:", [1, 2, 3], default=[1, 2, 3])
    
    st.header("2. Keepa Relevance (Optional)")
    target_asin = st.text_input("Target ASIN (e.g., B0...)")
    keepa_api_key = st.text_input("Keepa API Key", type="password")
    st.caption("If provided, the app will label terms as 'Relevant' or 'Irrelevant'.")

# Main Interface
uploaded_file = st.file_uploader("Upload Amazon Bulk File (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        with st.spinner("Processing Bulk File and Generating N-Grams..."):
            sp_df, sb_df = load_bulk_file(uploaded_file)
            aggregated_df = aggregate_data(sp_df, sb_df)
            
            results = {}
            for size in ngram_sizes:
                results[size] = perform_ngram_analysis(aggregated_df, size)

            if target_asin and keepa_api_key:
                st.info(f"Connecting to Keepa for ASIN: {target_asin}...")
                analyzer = KeepaRelevanceAnalyzer(keepa_api_key)
                product_data = analyzer.fetch_product_data(target_asin)
                
                if product_data:
                    product_keywords = analyzer.extract_keywords(product_data)
                    for size in results:
                        results[size]['Relevance'] = results[size]['Term'].apply(
                            lambda x: analyzer.analyze_relevance(x, product_keywords)
                        )
                else:
                    st.error("Could not fetch Keepa data. Check your ASIN or API Key.")

        # Display results in columns
        st.divider()
        cols = st.columns(len(ngram_sizes))
        for idx, size in enumerate(ngram_sizes):
            with cols[idx]:
                st.subheader(f"{size}-Grams")
                st.dataframe(results[size].head(20), use_container_width=True)

        # Excel Export Logic
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for size, df in results.items():
                df.to_excel(writer, sheet_name=f"{size}-Gram Analysis", index=False)
        
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Full Analysis (Excel)",
            data=processed_data,
            file_name=f"PPC_Analysis_{target_asin if target_asin else 'Report'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Analysis ready!")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Check if your Excel file has 'SP Search Term Report' and 'SB Search Term Report' tabs.")
