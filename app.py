import streamlit as st
import pandas as pd
import io
import os
from analyzer import load_bulk_file, aggregate_data, perform_ngram_analysis
from keepa_relevance_analyzer import KeepaRelevanceAnalyzer

# Page configuration for a professional wide-screen layout
st.set_page_config(page_title="PPC Negative Keyword Analyzer", layout="wide")

st.title("🚀 Amazon PPC Negative Keyword Analyzer")
st.markdown("""
Upload your **Amazon Bulk File** to identify wasted ad spend through n-gram analysis. 
Optionally, connect to **Keepa** to automatically flag terms that do not match your product metadata.
""")

# Sidebar for User Configuration
with st.sidebar:
    st.header("1. Analysis Settings")
    # Allows user to choose which n-gram lengths to calculate
    ngram_sizes = st.multiselect("Select N-Grams to analyze:", [1, 2, 3], default=[1, 2, 3]) [cite: 126]
    
    st.header("2. Keepa Relevance (Optional)")
    # Inputs required for the KeepaRelevanceAnalyzer class [cite: 7, 127]
    target_asin = st.text_input("Target ASIN (e.g., B0...)") [cite: 126]
    keepa_api_key = st.text_input("Keepa API Key", type="password") [cite: 127]
    st.caption("Providing these will label terms as 'Relevant' or 'Irrelevant' based on product data.") [cite: 127]

# Main File Upload Interface
uploaded_file = st.file_uploader("Upload Amazon Bulk File (.xlsx)", type=["xlsx"]) [cite: 127]

if uploaded_file:
    try:
        with st.spinner("Processing Bulk File and Generating N-Grams..."):
            # Load SP and SB reports and aggregate metrics [cite: 122, 123, 128]
            sp_df, sb_df = load_bulk_file(uploaded_file)
            aggregated_df = aggregate_data(sp_df, sb_df)
            
            # Perform n-gram analysis for each selected size [cite: 124, 125, 128]
            results = {}
            for size in ngram_sizes:
                results[size] = perform_ngram_analysis(aggregated_df, size)

            # Integrate Keepa Relevance if credentials are provided [cite: 128, 129]
            if target_asin and keepa_api_key:
                st.info(f"Connecting to Keepa for ASIN: {target_asin}...")
                analyzer = KeepaRelevanceAnalyzer(keepa_api_key)
                product_data = analyzer.fetch_product_data(target_asin) [cite: 129]
                
                if product_data:
                    # Extract product keywords for matching [cite: 129]
                    product_keywords = analyzer.extract_keywords(product_data)
                    for size in results:
                        # Apply relevance labeling to each n-gram [cite: 130, 131]
                        results[size]['Relevance'] = results[size]['Term'].apply(
                            lambda x: analyzer.analyze_relevance(x, product_keywords)
                        )
                else:
                    st.error("Could not fetch Keepa data. Check your ASIN or API Key.") [cite: 131, 132]

        # Display Previews in adaptive columns [cite: 132]
        st.divider()
        cols = st.columns(len(ngram_sizes))
        for idx, size in enumerate(ngram_sizes):
            with cols[idx]:
                st.subheader(f"{size}-Grams")
                # Show top 20 terms by spend for quick review [cite: 133]
                st.dataframe(results[size].head(20), use_container_width=True)

        # Prepare Excel Export using a buffer for web download [cite: 133]
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for size, df in results.items():
                # Each n-gram size gets its own tab in the Excel file [cite: 133]
                df.to_excel(writer, sheet_name=f"{size}-Gram Analysis", index=False)
        
        processed_data = output.getvalue() [cite: 134]

        # Provide a download button for the final report [cite: 134]
        st.download_button(
            label="📥 Download Full Analysis (Excel)",
            data=processed_data,
            file_name=f"PPC_Analysis_{target_asin if target_asin else 'Report'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Analysis complete and ready for download!") [cite: 134]

    except Exception as e:
        # Standard error handling if the bulk file format is incorrect [cite: 135]
        st.error(f"An error occurred: {e}")
        st.info("Ensure your file has 'SP Search Term Report' and 'SB Search Term Report' tabs.") [cite: 135]
