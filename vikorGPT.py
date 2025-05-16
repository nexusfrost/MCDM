import streamlit as st
import numpy as np
import pandas as pd

def calculate_vikor(data, weights, criteria_types, v=0.5):
    """Calculate VIKOR scores for decision matrix"""
    # Convert weights to numpy array and normalize
    weights = np.array(weights)
    weights /= weights.sum()
    
    # Determine best and worst values
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
    
    # Handle zero divisions
    diff = best - worst
    diff[diff == 0] = 1e-9  # Avoid division by zero
    
    # Calculate S and R values
    S = []
    R = []
    for _, row in data.iterrows():
        weighted_dist = weights * (best - row.values) / diff
        S.append(weighted_dist.sum())
        R.append(weighted_dist.max())
    
    # Calculate Q values
    S = np.array(S)
    R = np.array(R)
    S_min, S_max = S.min(), S.max()
    R_min, R_max = R.min(), R.max()
    
    Q = v * (S - S_min)/(S_max - S_min + 1e-9) + (1 - v) * (R - R_min)/(R_max - R_min + 1e-9)
    
    return pd.DataFrame({
        'Alternative': data.index,
        'S': S,
        'R': R,
        'Q': Q
    }).set_index('Alternative')

# Streamlit interface
st.title('VIKOR Method Implementation')
st.write("Upload your decision matrix CSV file (alternatives as rows, criteria as columns)")

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col=0)
    st.subheader("Decision Matrix")
    st.dataframe(df)
    
    criteria = df.columns.tolist()
    criteria_types = []
    weights = []
    
    st.subheader("Criteria Configuration")
    cols = st.columns(2)
    
    with cols[0]:
        st.markdown("**Criteria Directions**")
        for crit in criteria:
            criteria_types.append(st.selectbox(
                f"{crit} direction", 
                ['max', 'min'], 
                key=f"dir_{crit}"
            ))
    
    with cols[1]:
        st.markdown("**Criteria Weights**")
        for crit in criteria:
            weights.append(st.number_input(
                f"Weight for {crit}",
                min_value=0.0,
                max_value=1.0,
                value=1.0/len(criteria),
                step=0.01,
                key=f"weight_{crit}"
            ))
    
    v = st.slider("Compromise coefficient (v)", 0.0, 1.0, 0.5, 0.01)
    
    if st.button("Calculate VIKOR Scores"):
        try:
            results = calculate_vikor(df, weights, criteria_types, v)
            st.subheader("VIKOR Results")
            st.dataframe(results.sort_values('Q'))
            
            st.subheader("Ranking")
            ranking = results['Q'].rank().astype(int)
            st.write(ranking)
            
        except Exception as e:
            st.error(f"Error in calculation: {str(e)}")
