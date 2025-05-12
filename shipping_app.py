import streamlit as st
import pandas as pd
from difflib import get_close_matches
import plotly.express as px

st.set_page_config(page_title="📦 Shipping Rates Analyzer", layout="wide")
st.title("📦 Shipping Rates Analyzer")

uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["csv", "xlsx", "json", "txt"])

# Column keyword mapping dictionary
target_columns = {
    'POL': ['pol', 'port of loading', 'loading port'],
    'POD': ['pod', 'port of discharge', 'destination port'],
    "20'DC": ['20', "20'dc", '20ft', '20-foot', '20dc'],
    "40'DC/HC": ['40', "40'dc", '40hc', '40ft', '40-foot', '40dc'],
    "LTHC'20": ['lthc 20', 'local 20'],
    "LTHC'40": ['lthc 40', 'local 40'],
    'CURRENCY': ['currency', 'curr'],
    'F.TIME': ['freetime', 'f.time', 'f time', 'transit time', 'duration'],
    'REMARKS': ['remarks', 'note', 'comment', 'free days', 'free days at pod'],
    'CARRIER': ['carrier', 'carriers', 'shipping line', 'line', 'operator', 'transporter', 'service provider'],
    'VALIDITY': ['validity', 'valid until', 'valid to', 'valid thru', 'rate valid', 'rate expiry']
}

def smart_map_columns(df):
    mapped_cols = {}
    lower_cols = {col: col.lower().strip() for col in df.columns}

    for target, keywords in target_columns.items():
        found = None
        for orig_col, col_clean in lower_cols.items():
            if any(keyword in col_clean for keyword in keywords):
                found = orig_col
                break
        if not found:
            matches = get_close_matches(target.lower(), lower_cols.values(), n=1, cutoff=0.6)
            if matches:
                match_val = matches[0]
                for orig_col, col_clean in lower_cols.items():
                    if col_clean == match_val:
                        found = orig_col
                        break
        if found:
            mapped_cols[found] = target

    df.rename(columns=mapped_cols, inplace=True)
    return df

def clean_data(df):
    # Convert rates to numeric where possible
    df["20'DC"] = pd.to_numeric(df["20'DC"], errors='coerce')
    df["40'DC/HC"] = pd.to_numeric(df["40'DC/HC"], errors='coerce')
    df['POL'] = df['POL'].str.strip().str.upper()
    df['POD'] = df['POD'].str.strip().str.upper()
    return df

def to_csv(df):
    return df.to_csv(index=False)

if uploaded_file:
    try:
        with st.spinner('Processing data...'):
            # Read uploaded file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                df = pd.read_json(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Clean and standardize column names
            df.columns = df.columns.str.strip().str.upper()

            # Map columns to standard names
            df = smart_map_columns(df)
            df = clean_data(df)

            # Ensure required columns exist
            required_columns = ['POL', 'POD']
            for col in required_columns:
                if col not in df.columns:
                    suggestions = get_close_matches(col, df.columns, n=1, cutoff=0.6)
                    if suggestions:
                        df.rename(columns={suggestions[0]: col}, inplace=True)
                        st.info(f"🔄 Auto-mapped '{suggestions[0]}' to '{col}'")

            # Manual fallback mapping
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.warning("Some required columns are missing. Please map them manually:")
                for col in missing_cols:
                    selected = st.selectbox(f"Select a column to use as '{col}':", df.columns, key=col)
                    df.rename(columns={selected: col}, inplace=True)

            # Final required check
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.error(f"❌ The following required columns are still missing: {missing_cols}")
            else:
                # Clean up values
                df.dropna(subset=['POL', 'POD'], inplace=True)

                # POL selection
                pol_options = sorted(df['POL'].unique())
                selected_pol = st.selectbox("Select Port of Loading (POL):", pol_options)

                if selected_pol:
                    df_filtered = df[df['POL'] == selected_pol]

                    # POD selection
                    pod_options = sorted(df_filtered['POD'].unique())
                    selected_pod = st.selectbox("Select Port of Discharge (POD):", pod_options)

                    if selected_pod:
                        final_df = df_filtered[df_filtered['POD'] == selected_pod]

                        # Columns to display
                        columns_to_show = [
                            'POL', 'POD',
                            "20'DC", "40'DC/HC",
                            "LTHC'20", "LTHC'40",
                            'CURRENCY', 'F.TIME', 'REMARKS', 'VALIDITY'
                        ]
                        if 'CARRIER' in final_df.columns:
                            columns_to_show.insert(2, 'CARRIER')  # Show after POD

                        available_cols = [col for col in columns_to_show if col in final_df.columns]

                        if not final_df.empty:
                            st.subheader(f"📊 All Shipping Options: {selected_pol} ➡ {selected_pod}")
                            st.dataframe(final_df[available_cols], use_container_width=True)

                            # Highlighting best price for 20'DC and 40'DC/HC
                            best_20dc_row = final_df.loc[final_df["20'DC"].idxmin()]
                            best_40dc_row = final_df.loc[final_df["40'DC/HC"].idxmin()]
                            st.write("🔹 Best 20'DC price:", best_20dc_row)
                            st.write("🔹 Best 40'DC/HC price:", best_40dc_row)

                            # Plotting the comparison of prices
                            if "20'DC" in final_df.columns and "40'DC/HC" in final_df.columns:
                                fig = px.bar(final_df, x='POL', y=["20'DC", "40'DC/HC"], title="Shipping Rate Comparison")
                                st.plotly_chart(fig)

                        else:
                            st.warning("No data found for this route.")

                # Optional raw data
                if st.checkbox("📄 Show raw uploaded data"):
                    st.dataframe(df, use_container_width=True)

                # Allow the user to download filtered data
                st.download_button(
                    label="Download Filtered Data",
                    data=to_csv(final_df),
                    file_name="filtered_shipping_data.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
