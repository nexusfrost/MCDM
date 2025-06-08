import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="VIKOR Method with Manual & File Input", layout="wide")

# --- VIKOR CALCULATION FUNCTION ---
def calculate_vikor(data, weights, criteria_types, v=0.5):
    weights = np.array(weights)
    weights /= weights.sum()

    best = []
    worst = []
    for i, col in enumerate(data.columns):
        if criteria_types[i] == 'max':
            best.append(data[col].max())
            worst.append(data[col].min())
        else:
            best.append(data[col].min())
            worst.append(data[col].max())

    best = np.array(best)
    worst = np.array(worst)

    diff = best - worst
    diff[diff == 0] = 1e-9

    S, R = [], []
    for _, row in data.iterrows():
        weighted_dist = weights * (best - row.values) / diff
        S.append(weighted_dist.sum())
        R.append(weighted_dist.max())

    S = np.array(S)
    R = np.array(R)
    S_min, S_max = S.min(), S.max()
    R_min, R_max = R.min(), R.max()

    Q = v * (S - S_min) / (S_max - S_min + 1e-9) + (1 - v) * (R - R_min) / (R_max - R_min + 1e-9)

    return pd.DataFrame({
        'Alternative': data.index,
        'S': S,
        'R': R,
        'Q': Q
    }).set_index('Alternative')

# --- SESSION STATE INITIALIZATION ---
if 'criteria' not in st.session_state:
    st.session_state.criteria = []
if 'criteria_types' not in st.session_state:
    st.session_state.criteria_types = []
if 'weights' not in st.session_state:
    st.session_state.weights = []
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()

# --- TITLE ---
st.title("VIKOR: Supplier")

# --- FILE UPLOAD SECTION ---
st.header("Step 1: Upload File (Optional)")
uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, index_col=0)
        else:
            df = pd.read_excel(uploaded_file, index_col=0)
        st.session_state.data = df
        st.success("File uploaded and loaded successfully.")
    except Exception as e:
        st.error(f"Failed to read file: {str(e)}")

# --- CRITERIA SETUP ---
st.header("Step 2: Define Criteria")

with st.expander("Add New Criterion"):
    new_criterion = st.text_input("Criterion name")
    direction = st.selectbox("Direction", ['max', 'min'])
    weight = st.number_input("Weight", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
    if st.button("Add Criterion"):
        if new_criterion and new_criterion not in st.session_state.criteria:
            st.session_state.criteria.append(new_criterion)
            st.session_state.criteria_types.append(direction)
            st.session_state.weights.append(weight)
            st.success(f"Added criterion: {new_criterion}")
        else:
            st.warning("Criterion name must be unique and non-empty.")

# --- ALTERNATIVE INPUT SECTION ---
st.header("Step 3: Add Alternatives Manually")
if st.session_state.criteria:
    with st.form("add_alternative"):
        name = st.text_input("Alternative name")
        values = []
        for crit in st.session_state.criteria:
            val = st.number_input(f"Value for {crit}", step=0.01)
            values.append(val)
        submitted = st.form_submit_button("Add Alternative")
        if submitted:
            if name:
                row = pd.DataFrame([values], columns=st.session_state.criteria, index=[name])
                st.session_state.data = pd.concat([st.session_state.data, row])
                st.success(f"Added alternative: {name}")
            else:
                st.warning("Alternative name cannot be empty.")

# --- SHOW CURRENT MATRIX ---
if not st.session_state.data.empty:
    st.subheader("Current Decision Matrix")
    st.dataframe(st.session_state.data)

# --- VIKOR CALCULATION ---
if not st.session_state.data.empty and st.button("Calculate VIKOR Scores"):
    try:
        v = st.slider("Compromise coefficient (v)", 0.0, 1.0, 0.5, 0.01)
        result = calculate_vikor(
            st.session_state.data,
            st.session_state.weights,
            st.session_state.criteria_types,
            v
        )
        st.subheader("VIKOR Results")
        st.dataframe(result.sort_values('Q'))

        st.subheader("Ranking")
        ranking = result['Q'].rank().astype(int)
        st.write(ranking)
    except Exception as e:
        st.error(f"Error during VIKOR calculation: {str(e)}")
