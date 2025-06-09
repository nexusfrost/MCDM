import streamlit as st
import pandas as pd
import numpy as np

st.title("MCDM with PROMETHEE Method")

if "page" not in st.session_state:
    st.session_state.page = "criteria_input"
if "criteria_with_weights" not in st.session_state:
    st.session_state.criteria_with_weights = []
if "suppliers" not in st.session_state:
    st.session_state.suppliers = []

# PAGE 1: Input kriteria
if st.session_state.page == "criteria_input":
    st.header("Step 1: Define Criteria and Weights")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_criterion = st.text_input("Criterion name")
    with col2:
        weight = st.number_input("Weight", 0.0, 100.0, step=1.0)

    total_weight = sum(c["weight"] for c in st.session_state.criteria_with_weights)

    if st.button("Add Criterion with Weight"):
        if not new_criterion:
            st.warning("Criterion name cannot be empty.")
        elif any(c["name"] == new_criterion for c in st.session_state.criteria_with_weights):
            st.warning("This criterion already exists.")
        elif total_weight + weight > 100:
            st.error("Total weight exceeds 100.")
        else:
            st.session_state.criteria_with_weights.append({
                "name": new_criterion,
                "weight": weight
            })

    st.subheader("Current Criteria")
    for c in st.session_state.criteria_with_weights:
        st.write(f"- {c['name']} (Weight: {c['weight']})")
    st.write(f"Total weight: {sum(c['weight'] for c in st.session_state.criteria_with_weights)}")

    if sum(c['weight'] for c in st.session_state.criteria_with_weights) == 100:
        if st.button("Next"):
            st.session_state.page = "edit_criteria"

# Page 2 Weight setiap kriteria
elif st.session_state.page == "edit_criteria":
    st.header("Step 2: Define Weigth for Each Criterion")

    for idx, criterion in enumerate(st.session_state.criteria_with_weights):
        with st.expander(f"{criterion['name']} (Weight: {criterion['weight']})"):
            if f"levels_{idx}" not in st.session_state:
                st.session_state[f"levels_{idx}"] = []

            col1, col2 = st.columns([2, 1])
            with col1:
                level_label = st.text_input("Level name", key=f"level_label_{idx}")
            with col2:
                level_score = st.number_input("Score", 0.0, step=1.0, key=f"level_score_{idx}")

            if st.button("Add Level", key=f"add_level_{idx}"):
                if level_label:
                    st.session_state[f"levels_{idx}"].append({
                        "label": level_label,
                        "score": level_score
                    })

            st.markdown("**Defined Levels:**")
            for lvl in st.session_state[f"levels_{idx}"]:
                st.write(f"- {lvl['label']} (Score: {lvl['score']})")

            st.session_state.criteria_with_weights[idx]["levels"] = st.session_state[f"levels_{idx}"]

    if st.button("Next: Add Suppliers"):
        st.session_state.page = "input_alternatives"

# Page 3 Input Supplier
elif st.session_state.page == "input_alternatives":
    st.header("Step 3: Add Suppliers and Assign Levels")

    supplier_name = st.text_input("Supplier name")
    if st.button("Add Supplier"):
        if not supplier_name:
            st.warning("Supplier name cannot be empty.")
        elif any(s["name"] == supplier_name for s in st.session_state.suppliers):
            st.warning("Supplier already exists.")
        else:
            st.session_state.suppliers.append({
                "name": supplier_name,
                "selections": {c["name"]: "" for c in st.session_state.criteria_with_weights}
            })

    if st.session_state.suppliers:
        for s_idx, supplier in enumerate(st.session_state.suppliers):
            with st.expander(f"Supplier: {supplier['name']}"):
                for c in st.session_state.criteria_with_weights:
                    levels = c.get("levels", [])
                    options = [lvl["label"] for lvl in levels]
                    if not options:
                        continue
                    selected_level = st.selectbox(
                        c["name"],
                        options=options,
                        key=f"select_{s_idx}_{c['name']}"
                    )
                    st.session_state.suppliers[s_idx]["selections"][c["name"]] = selected_level

    if st.button("Show Evaluation Matrix"):
        st.session_state.page = "show_results"

# Page 4 Hasil Promethee
elif st.session_state.page == "show_results":
    st.header("Step 4: Evaluation Matrix")

    import pandas as pd
    import numpy as np

    # === Build Evaluation Matrix ===
    matrix_data = []
    row_labels = []

    for supplier in st.session_state.suppliers:
        row = {}
        row_labels.append(supplier["name"])
        for criterion in st.session_state.criteria_with_weights:
            selected_level = supplier["selections"].get(criterion["name"], "")
            level_score = next((lvl["score"] for lvl in criterion.get("levels", [])
                                if lvl["label"] == selected_level), 0)
            row[criterion["name"]] = level_score
        matrix_data.append(row)

    df = pd.DataFrame(matrix_data, index=row_labels)
    
    display_df = df.copy()
    renamed_columns = {
        criterion["name"]: f"{criterion['name']} ({ ['weight']}%)"
        for criterion in st.session_state.criteria_with_weights
    }
    display_df.rename(columns=renamed_columns, inplace=True)

    st.subheader("Evaluation Matrix")
    st.dataframe(display_df.style.format(precision=2), use_container_width=True)

    # === Compute Pairwise Preference Index Matrix ===
    st.subheader("Preference Index Matrix (PROMETHEE)")

    suppliers = df.index.tolist()
    n = len(suppliers)
    preference_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            preference_score = 0
            for criterion in st.session_state.criteria_with_weights:
                name = criterion["name"]
                weight = criterion["weight"] / 100
                val_i = df.iloc[i][name]
                val_j = df.iloc[j][name]
                d = val_i - val_j

                # Usual preference function (linear scaling)
                h = 0
                if d > 0:
                    h = 1
                elif d == 0:
                    h = 0
                else:
                    h = 0  # No preference if worse

                preference_score += weight * h

            preference_matrix[i][j] = round(preference_score, 3)

    preference_df = pd.DataFrame(preference_matrix, index=suppliers, columns=suppliers)
    st.dataframe(preference_df.style.format(precision=3), use_container_width=True)


    suppliers = row_labels
    n = len(suppliers)
    weights = {c["name"]: c["weight"] / 100 for c in st.session_state.criteria_with_weights}
    preference_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            total_pref = 0
            for criterion in st.session_state.criteria_with_weights:
                name = criterion["name"]
                d = df.iloc[i][name] - df.iloc[j][name]
                h = 1 if d > 0 else 0
                total_pref += weights[name] * h
            preference_matrix[i, j] = total_pref

    leaving_flow = preference_matrix.sum(axis=1) / (n - 1)
    entering_flow = preference_matrix.sum(axis=0) / (n - 1)
    net_flow = leaving_flow - entering_flow

    result_df = pd.DataFrame({
        "Supplier": suppliers,
        "Leaving Flow (ϕ⁺)": leaving_flow,
        "Entering Flow (ϕ⁻)": entering_flow,
        "Net Flow (ϕ)": net_flow
    })

    # Add Ranking
    result_df["Rank"] = result_df["Net Flow (ϕ)"].rank(ascending=False, method="min").astype(int)

    # Sort by Net Flow for final presentation
    result_df = result_df.sort_values(by="Net Flow (ϕ)", ascending=False).reset_index(drop=True)

    # Detailed Comparison Section
    with st.expander("Pairwise Comparisons by Criterion"):
        for criterion in st.session_state.criteria_with_weights:
            name = criterion["name"]
            st.write(f"### Criterion: {name}")
            table = []
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    val_i = df.iloc[i][name]
                    val_j = df.iloc[j][name]
                    d = val_i - val_j
                    h = 1 if d > 0 else 0
                    table.append({
                        "Comparison": f"{suppliers[i]} vs {suppliers[j]}",
                        "d": f"{val_i:.1f} - {val_j:.1f} = {d:.1f}",
                        "H(d)": h
                    })
            st.dataframe(pd.DataFrame(table), use_container_width=True)

    st.subheader("Final PROMETHEE Ranking")
    st.dataframe(result_df.style.format(precision=3), use_container_width=True)