import streamlit as st
import pandas as pd

st.title("📦 Shipping Rates Analyzer")

# Upload file
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["csv", "xlsx"])

# If the file is uploaded
if uploaded_file:
    try:
        # Read the file based on its type (CSV or Excel)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Clean column names (strip any leading/trailing spaces)
        df.columns = df.columns.str.strip()

        # Rename any incorrect column names (e.g., "CURRENCEY" to "CURRENCY")
        if 'CURRENCEY' in df.columns:
            df.rename(columns={'CURRENCEY': 'CURRENCY'}, inplace=True)

        # Drop rows with empty values in crucial columns: POL, POD, and CARRIER
        df.dropna(subset=['POL', 'POD', 'CARRIER'], inplace=True)

        # Normalize POL and POD columns: strip spaces and make uppercase
        df['POL'] = df['POL'].str.strip().str.upper()
        df['POD'] = df['POD'].str.strip().str.upper()

        # Get unique POL options and display as a dropdown
        pol_options = sorted(df['POL'].dropna().unique())
        selected_pol = st.selectbox("Select Port of Loading (POL):", pol_options)

        # Filter the dataframe by the selected POL
        if selected_pol:
            filtered_df = df[df['POL'] == selected_pol.upper()]

            # Get unique POD options based on the selected POL
            pod_options = sorted(filtered_df['POD'].dropna().unique())
            selected_pod = st.selectbox("Select Port of Discharge (POD):", pod_options)

            # Filter the dataframe further by the selected POD
            if selected_pod:
                final_filtered_df = filtered_df[filtered_df['POD'] == selected_pod.upper()]

                # Group by POL, POD, and CARRIER to merge duplicates, selecting the minimum price
                grouped_df = final_filtered_df.groupby(['POL', 'POD', 'CARRIER'], as_index=False).agg({
                    "20'DC": 'min',   # Take the minimum 20'DC cost
                    "40'DC/HC": 'min', # Take the minimum 40'DC/HC cost
                    'CURRENCY': 'first',  # Assuming all entries have the same currency
                    'F.TIME': 'first',  # Assuming the first "F.TIME" is fine for all entries
                    'REMARKS': 'first'   # Take the first remark (you can modify if needed)
                })

                if not grouped_df.empty:
                    # Display results
                    st.subheader(f"📦 Shipping Options from {selected_pol.upper()} to {selected_pod.upper()}")
                    
                    # Display sorted by 20'DC prices (cheapest first)
                    st.subheader("🔹 Sorted by Cheapest 20'DC Prices")
                    st.dataframe(grouped_df[['POD', 'CARRIER', "20'DC", 'CURRENCY', 'F.TIME', 'REMARKS']].sort_values(by="20'DC"))

                    # Display sorted by 40'DC/HC prices (cheapest first)
                    st.subheader("🔹 Sorted by Cheapest 40'DC/HC Prices")
                    st.dataframe(grouped_df[['POD', 'CARRIER', "40'DC/HC", 'CURRENCY', 'F.TIME', 'REMARKS']].sort_values(by="40'DC/HC"))
                else:
                    st.warning(f"No results found for {selected_pol} to {selected_pod}")
        
        # Add feature to show raw data
        if st.checkbox("Show raw data"):
            st.subheader("Raw Data")
            st.write(df)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
