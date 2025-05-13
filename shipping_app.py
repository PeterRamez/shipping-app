import streamlit as st
import pandas as pd
from difflib import get_close_matches
import plotly.express as px

st.set_page_config(page_title="📦 Shipping Rates Analyzer", layout="wide")
st.title("📦 Shipping Rates Analyzer")

uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["csv", "xlsx", "json", "txt"])

# Updated column keyword mapping
target_columns = {
    'POL': ['pol', 'port of loading', 'loading port'],
    'POD': ['pod', 'port of discharge', 'destination port'],
    "20'DC": ['20', "20'dc", '20ft', '20-foot', '20dc'],
    "40'DC/HC": ['40', "40'dc", '40hc', '40ft', '40-foot', '40dc'],
    "LTHC'20": ['lthc 20', 'local 20'],
    "LTHC'40": ['lthc 40', 'local 40'],
    'CURRENCY': ['currency', 'curr'],
    'F.TIME': ['freetime', 'f.time', 'f time', 'free time'],
    'TRANSIT.TIME': ['transit time', 't.t approximately', 'tt approximately', 't/t approx', 'transit approx'],
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
    if "20'DC" in df.columns:
        df["20'DC"] = pd.to_numeric(df["20'DC"], errors='coerce')
    if "40'DC/HC" in df.columns:
        df["40'DC/HC"] = pd.to_numeric(df["40'DC/HC"], errors='coerce')
    if 'POL' in df.columns:
        df['POL'] = df['POL'].astype(str).str.strip().str.upper()
    if 'POD' in df.columns:
        df['POD'] = df['POD'].astype(str).str.strip().str.upper()
    return df

def to_csv(df):
    return df.to_csv(index=False)

if uploaded_file:
    try:
        with st.spinner('Processing data...'):
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                df = pd.read_json(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            df.columns = df.columns.str.strip().str.upper()
            df = smart_map_columns(df)
            df = clean_data(df)

            if 'POL' not in df.columns or 'POD' not in df.columns:
                st.error("❌ File must contain at least 'POL' and 'POD' columns to continue.")
            else:
                df.dropna(subset=['POL', 'POD'], inplace=True)

                pol_options = sorted(df['POL'].unique())
                selected_pol = st.selectbox("Select Port of Loading (POL):", pol_options)

                if selected_pol:
                    df_filtered = df[df['POL'] == selected_pol]
                    pod_options = sorted(df_filtered['POD'].unique())
                    selected_pod = st.selectbox("Select Port of Discharge (POD):", pod_options)

                    if selected_pod:
                        final_df = df_filtered[df_filtered['POD'] == selected_pod]

                        if not final_df.empty:
                            st.subheader("Choose what you want to analyze:")
                            choice = st.radio("Select Analysis Type", ["Best Price", "Best Transit Time"])

                            if choice == "Best Price":
                                st.markdown(f"### 📍 Best Prices for {selected_pol} ➡ {selected_pod}")

                                if "20'DC" in final_df.columns and final_df["20'DC"].notna().any():
                                    best_20dc = final_df.loc[final_df["20'DC"].idxmin()]
                                    st.markdown("#### 🔹 Best 20'DC")
                                    st.write(best_20dc[best_20dc.index.intersection(['POL', 'POD', 'CARRIER', "20'DC", "LTHC'20", 'CURRENCY', 'F.TIME', 'TRANSIT.TIME', 'VALIDITY', 'REMARKS'])])
                                else:
                                    st.warning("⚠️ 20'DC column not available.")

                                if "40'DC/HC" in final_df.columns and final_df["40'DC/HC"].notna().any():
                                    best_40dc = final_df.loc[final_df["40'DC/HC"].idxmin()]
                                    st.markdown("#### 🔹 Best 40'DC/HC")
                                    st.write(best_40dc[best_40dc.index.intersection(['POL', 'POD', 'CARRIER', "40'DC/HC", "LTHC'40", 'CURRENCY', 'F.TIME', 'TRANSIT.TIME', 'VALIDITY', 'REMARKS'])])
                                else:
                                    st.warning("⚠️ 40'DC/HC column not available.")

                            elif choice == "Best Transit Time":
                                if 'TRANSIT.TIME' in final_df.columns:
                                    final_df['TRANSIT_TIME_NUM'] = pd.to_numeric(
                                        final_df['TRANSIT.TIME'].astype(str).str.extract(r'(\d+)')[0],
                                        errors='coerce'
                                    )
                                    if final_df['TRANSIT_TIME_NUM'].notna().any():
                                        best_transit = final_df.loc[final_df['TRANSIT_TIME_NUM'].idxmin()]
                                        st.markdown(f"### 🚀 Fastest Transit Time for {selected_pol} ➡ {selected_pod}")
                                        st.write(best_transit[best_transit.index.intersection(['POL', 'POD', 'CARRIER', "20'DC", "40'DC/HC", 'TRANSIT.TIME', 'CURRENCY', 'VALIDITY', 'REMARKS'])])
                                    else:
                                        st.warning("⚠️ Could not extract transit time as numeric value.")
                                else:
                                    st.warning("⚠️ 'TRANSIT.TIME' column not available.")

                if st.checkbox("📄 Show raw uploaded data"):
                    st.dataframe(df, use_container_width=True)

                st.download_button(
                    label="Download Filtered Data",
                    data=to_csv(df),
                    file_name="filtered_shipping_data.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
