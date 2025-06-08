import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="VIKOR Method", layout="wide")

def calculate_vikor(data, weights, criteria_types, v=0.5):
    weights = np.array(weights)
    weights /= weights.sum()

    # Cari Terendah/Tertinggi
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

    # Perbedaan
    diff = best - worst
    diff[diff == 0] = 1e-9

    # Cari Q
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

if 'criteria' not in st.session_state:
    st.session_state.criteria = []
if 'criteria_types' not in st.session_state:
    st.session_state.criteria_types = []
if 'weights' not in st.session_state:
    st.session_state.weights = []
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()

st.title("VIKOR: Supplier")

# Kriteria
st.header("Step 1: Input Kriteria")

with st.expander("Tambahkan Kriteria"):
    new_criterion = st.text_input("Kriteria")
    direction = st.selectbox("Beneficial/Non Beneficial", ['max', 'min'])
    weight = st.number_input("Weight", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
    if st.button("SAVE"):
        if new_criterion and new_criterion not in st.session_state.criteria:
            st.session_state.criteria.append(new_criterion)
            st.session_state.criteria_types.append(direction)
            st.session_state.weights.append(weight)
            st.success(f"Berhasil Menambahkan: {new_criterion}")
        else:
            st.warning("Nama Kriteria Harus Unik")

# Alternatif
st.header("Step 2: Tambahkan Alternatif")
if st.session_state.criteria:
    with st.form("add_alternative"):
        name = st.text_input("Alternatif")
        values = []
        for crit in st.session_state.criteria:
            val = st.number_input(f"Value for {crit}", step=0.01)
            values.append(val)
        submitted = st.form_submit_button("SAVE")
        if submitted:
            if name:
                row = pd.DataFrame([values], columns=st.session_state.criteria, index=[name])
                st.session_state.data = pd.concat([st.session_state.data, row])
                st.success(f"Berhasil Menambahkan Alternatif: {name}")
            else:
                st.warning("Alternatif harus unik")

# Matrix Sekarang
if not st.session_state.data.empty:
    st.subheader("Current Decision Matrix")
    st.dataframe(st.session_state.data)

# Menghitung VIKOR
if not st.session_state.data.empty and st.button("Calculate VIKOR Scores"):
    try:
        v = st.slider("Compromise coefficient (v)", 0.0, 1.0, 0.5, 0.01)
        result = calculate_vikor(
            st.session_state.data,
            st.session_state.weights,
            st.session_state.criteria_types,
            v
        )
        st.subheader("VIKOR Ranking")

        # Sort Q
        result_sorted = result.sort_values('Q')
        result_sorted['Rank'] = range(1, len(result_sorted) + 1)
        st.dataframe(result_sorted)

        # Kompromi Pilihan
        m = len(result_sorted)
        DQ = 1 / (m - 1) if m > 1 else 0
        Q_values = result_sorted['Q'].values
        S_values = result_sorted['S'].values
        R_values = result_sorted['R'].values
        alternatives = result_sorted.index.tolist()

        st.write(f"**DQ :** {DQ:.4f}") 

        # Cari A1 dan A2
        A1 = alternatives[0]
        A2 = alternatives[1] if m > 1 else None

        # Acceptable Advantage
        acceptable_advantage = (Q_values[1] - Q_values[0]) >= DQ if m > 1 else True

        # Acceptable Stability
        S_best = S_values.argmin()
        R_best = R_values.argmin()
        acceptable_stability = (S_best == 0) or (R_best == 0)

        # Decision logic
        if acceptable_advantage and acceptable_stability:
            st.success(f"**Solusi Kompromi:** {A1}")
        elif acceptable_stability:
            st.info(f"**Solusi Kompromi:** {A1} and {A2}")
        else:
            # Find all alternatives with Q - Q(A1) < DQ
            close_alts = [alternatives[0]]
            for i in range(1, m):
                if (Q_values[i] - Q_values[0]) < DQ:
                    close_alts.append(alternatives[i])
            st.warning(f"**Solusi Kompromi:** {', '.join(close_alts)}")

    except Exception as e:
        st.error(f"Error : {str(e)}")

