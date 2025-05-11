import streamlit as st
import pandas as pd
from difflib import get_close_matches

st.set_page_config(page_title="📦 Shipping Rates Analyzer", layout="wide")
st.title("📦 Shipping Rates Analyzer")

uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["csv", "xlsx"])

# Keywords for flexible column mapping
target_columns = {
    'POL': ['pol', 'port of loading', 'loading port'],
    'POD': ['pod', 'port of discharge', 'destination port'],
    "20'DC": ['20', "20'dc", '20ft', '20-foot', '20dc'],
    "40'DC/HC": ['40', "40'dc", '40hc', '40ft', '40-foot', '40dc'],
    "LTHC'20": ['lthc 20', 'local 20'],
    "LTHC'40": ['lthc 40', 'local 40'],
    'CURRENCY': ['currency', 'curr'],
    'F.TIME': ['freetime', 'f.time', 'f time', 'transit time', 'duration'],
    'REMARKS': ['remarks', 'note', 'comment', 'free days', 'free days at pod']
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
            # fallback: fuzzy match
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

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.columns = df.columns.str.strip().str.upper()
        st.write("✅ Detected columns:", df.columns.tolist())

        # Apply smart mapping
        df = smart_map_columns(df)

        required_columns = ['POL', 'POD']
        for col in required_columns:
            if col not in df.columns:
                suggestions = get_close_matches(col, df.columns, n=1, cutoff=0.6)
                if suggestions:
                    df.rename(columns={suggestions[0]: col}, inplace=True)
                    st.info(f"🔄 Auto-mapped '{suggestions[0]}' to '{col}'")

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.warning("Some required columns are missing. Please map them manually:")
            for col in missing_cols:
                selected = st.selectbox(f"Select a column to use as '{col}':", df.columns, key=col)
                df.rename(columns={selected: col}, inplace=True)

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"❌ The following required columns are still missing: {missing_cols}")
        else:
            df.dropna(subset=['POL', 'POD'], inplace=True)
            df['POL'] = df['POL'].astype(str).str.strip().str.upper()
            df['POD'] = df['POD'].astype(str).str.strip().str.upper()

            pol_options = sorted(df['POL'].unique())
            selected_pol = st.selectbox("Select Port of Loading (POL):", pol_options)

            if selected_pol:
                df_filtered = df[df['POL'] == selected_pol]
                pod_options = sorted(df_filtered['POD'].unique())
                selected_pod = st.selectbox("Select Port of Discharge (POD):", pod_options)

                if selected_pod:
                    final_df = df_filtered[df_filtered['POD'] == selected_pod]

                    # Columns to show
                    columns_to_show = [
                        'POL', 'POD',
                        "20'DC", "40'DC/HC",
                        "LTHC'20", "LTHC'40",
                        'CURRENCY', 'F.TIME', 'REMARKS'
                    ]
                    available_cols = [col for col in columns_to_show if col in final_df.columns]

                    # Grouping logic
                    agg_funcs = {col: 'min' for col in ["20'DC", "40'DC/HC", "LTHC'20", "LTHC'40"] if col in final_df.columns}
                    for col in ['CURRENCY', 'F.TIME', 'REMARKS']:
                        if col in final_df.columns:
                            agg_funcs[col] = 'first'

                    grouped_df = final_df.groupby(['POL', 'POD'], as_index=False).agg(agg_funcs)

                    if not grouped_df.empty:
                        st.subheader(f"📊 Shipping Summary: {selected_pol} ➡ {selected_pod}")

                        if "20'DC" in grouped_df.columns:
                            st.subheader("🔹 Cheapest 20'DC Options")
                            st.dataframe(grouped_df.sort_values(by="20'DC")[available_cols])

                        if "40'DC/HC" in grouped_df.columns:
                            st.subheader("🔹 Cheapest 40'DC/HC Options")
                            st.dataframe(grouped_df.sort_values(by="40'DC/HC")[available_cols])
                    else:
                        st.warning("No data found for this route.")

            if st.checkbox("📄 Show raw uploaded data"):
                st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
