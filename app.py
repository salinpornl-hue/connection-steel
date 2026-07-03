# app.py
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. METRIC DATABASE & AISC J3 STANDARDS
# ==========================================
THAI_H_BEAM_PROFILES = {
    "H 200x200x8x12": {"d": 200.0, "bf": 200.0, "tw": 8.0, "tf": 12.0},
    "H 250x250x9x14": {"d": 250.0, "bf": 250.0, "tw": 9.0, "tf": 14.0},
    "H 300x300x10x15": {"d": 300.0, "bf": 300.0, "tw": 10.0, "tf": 15.0},
    "H 350x350x12x19": {"d": 350.0, "bf": 350.0, "tw": 12.0, "tf": 19.0},
    "H 400x400x13x21": {"d": 400.0, "bf": 400.0, "tw": 13.0, "tf": 21.0}
}

THAI_ANCHOR_BOLTS = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area": 157.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 22.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area": 245.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 26.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area": 353.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 32.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area": 561.0, "F_nt": 600.0, "F_nv": 360.0, "min_edge": 38.0},
    "M36 (Grade 8.8)": {"dia": 36.0, "area": 817.0, "F_nt": 600.0, "F_nv": 360.0, "min_edge": 46.0}
}

THAI_PLATE_THICKNESSES = [12, 16, 19, 22, 25, 28, 32, 38, 50]


def solve_bearing_block_bolts(P_u, M_u, B, N, bolt_coords, q_max):
    """Solve the coupled bearing-block + anchor-bolt equilibrium for a moment
    base plate in the uplift regime (AISC Design Guide 1, simplified method).
    """
    bolts = [(x, y) for (x, y) in bolt_coords]
    n = len(bolts)
    if n == 0:
        return {"ok": False, "case": "no-bolts", "tensions": []}

    Y_min = P_u / (q_max * B) if (q_max * B) > 0 else 0.0

    e = M_u / P_u if P_u > 0 else float("inf")
    if P_u > 0 and e <= N / 2.0:
        return {"ok": True, "case": "bearing-only", "Y": None, "C": P_u,
                "total_T": 0.0, "y_NA": None,
                "tensions": [0.0] * n, "resid_F": 0.0, "resid_M": 0.0}

    if Y_min >= N - 1.0:
        return {"ok": False, "case": "pu-too-large",
                "reason": "P_u exceeds max bearing (q_max*B*N); enlarge plate.",
                "tensions": [0.0] * n}

    def state(Y):
        y_NA = -N / 2.0 + Y
        tb = [y for (_, y) in bolts if y > y_NA + 1e-6]
        if not tb:
            return None
        C = q_max * B * Y
        arms = [y - y_NA for y in tb]
        k = max(0.0, (C - P_u) / sum(arms))
        Ts = [k * a for a in arms]
        M_resist = C * (N / 2.0 - Y / 2.0) + sum(T * y for T, y in zip(Ts, tb))
        return y_NA, tb, Ts, C, k, M_resist

    Y_lo, Y_hi = max(Y_min, 1.0), N - 1.0
    samples = 400
    grid = [Y_lo + (Y_hi - Y_lo) * i / samples for i in range(samples + 1)]
    st_grid = [state(Y) for Y in grid]
    resids = [(s[5] - M_u) if s else None for s in st_grid]

    solution = None
    for i in range(samples):
        r1, r2 = resids[i], resids[i + 1]
        if r1 is None or r2 is None:
            continue
        if (r1 >= 0) != (r2 >= 0):
            lo, hi = grid[i], grid[i + 1]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                sm = state(mid)
                rm = (sm[5] - M_u) if sm else r1
                rlo = state(lo)[5] - M_u
                if (rlo >= 0) != (rm >= 0):
                    hi = mid
                else:
                    lo = mid
            solution = state(0.5 * (lo + hi))
            Y_sol = 0.5 * (lo + hi)
            break

    if solution is None:
        return {"ok": False, "case": "insufficient-capacity",
                "reason": "Bearing + bolts cannot develop M_u; add bolts/plate/anchor capacity.",
                "tensions": [0.0] * n}

    y_NA, tb, Ts, C, k, _ = solution
    tensions = []
    ti = 0
    for (_, y) in bolts:
        if y > y_NA + 1e-6:
            tensions.append(Ts[ti] / 1000.0); ti += 1
        else:
            tensions.append(0.0)
    total_T = sum(Ts)
    resid_F = C - P_u - total_T
    resid_M = C * (N / 2.0 - Y_sol / 2.0) + sum(T * y for T, y in zip(Ts, tb)) - M_u
    return {"ok": True, "case": "uplift", "Y": Y_sol, "C": C, "k": k,
            "y_NA": y_NA, "total_T_kN": total_T / 1000.0,
            "tensions": tensions, "resid_F": resid_F, "resid_M": resid_M}


st.set_page_config(page_title="AISC Ultra-Matrix Connection Engine", layout="wide")

# CSS Styling - UI Refactoring
st.markdown("""
    <style>
    .main-title { font-size: 2.0rem; font-weight: 800; color: #1e293b; text-align: left; padding-bottom: 2px; }
    .sub-title { font-size: 0.95rem; color: #64748b; text-align: left; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    .column-title { background: #0f172a; color: white; padding: 10px 14px; border-radius: 6px 6px 0px 0px; font-weight: 600; font-size: 1.05rem; margin-bottom: 15px; border-left: 5px solid #3b82f6; }
    .rec-card { background-color: #f0fdf4; color: #14532d; padding: 15px; border-radius: 6px; border: 1px solid #bbf7d0; margin-bottom: 15px; font-size: 0.95rem; line-height: 1.5; }
    .danger-card { background-color: #fef2f2; color: #7f1d1d; padding: 15px; border-radius: 6px; border: 1px solid #fca5a5; margin-bottom: 15px; font-size: 0.9rem; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🛡️ AISC Steel-Connection Ultimate Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Independent bolt-group coordinate engine with edge-distance checks, steel-interference checks, and weld force distribution per AISC LRFD</div>", unsafe_allow_html=True)

# ==========================================
# 2. DEFINING THE 3-COLUMN STUDIO LAYOUT
# ==========================================
col_input, col_matrix, col_result = st.columns([0.9, 1.0, 1.1])

# ------------------------------------------
# COLUMN 1: STRUCTURAL INPUT PARAMETERS
# ------------------------------------------
with col_input:
    st.markdown("<div class='column-title'>🎛️ 1. Connection Section & Factored Loads</div>", unsafe_allow_html=True)

    selected_profile = st.selectbox("Connected steel column section (H-Beam TIS):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
    prof = THAI_H_BEAM_PROFILES[selected_profile]

    with st.container(border=True):
        st.caption("📐 Steel section dimensions (mm)")
        c1, c2 = st.columns(2)
        d = c1.number_input("Depth d", value=prof["d"])
        bf = c2.number_input("Flange width bf", value=prof["bf"])
        tw = c1.number_input("Web thickness tw", value=prof["tw"])
        tf = c2.number_input("Flange thickness tf", value=prof["tf"])

    with st.container(border=True):
        st.caption("⚡ Factored loads acting on the joint (LRFD Load)")
        cx1, cx2 = st.columns(2)
        p_u_kn = cx1.number_input("Axial comp. Pu (kN)", value=500.0)
        v_u_kn = cx2.number_input("Shear Vu (kN)", value=100.0)
        m_u_knm = cx1.number_input("Moment Mu (kN-m)", value=140.0)
        fc_mpa = cx2.number_input("Concrete f'c (MPa)", value=28.0)

    with st.container(border=True):
        st.caption("🔩 Base plate and anchor bolt sizes")
        rec_B = math.ceil((bf + 150) / 10) * 10
        rec_N = math.ceil((d + 160) / 10) * 10

        if "plate_version" not in st.session_state: st.session_state["plate_version"] = 0
        if "plate_B" not in st.session_state: st.session_state["plate_B"] = float(rec_B)
        if "plate_N" not in st.session_state: st.session_state["plate_N"] = float(rec_N)

        B = st.number_input("Plate width B (mm)", value=st.session_state["plate_B"], key=f"B_{st.session_state['plate_version']}")
        N = st.number_input("Plate length N (mm)", value=st.session_state["plate_N"], key=f"N_{st.session_state['plate_version']}")

        tp = st.selectbox("Plate thickness tp (mm)", THAI_PLATE_THICKNESSES, index=3)
        bolt_name = st.selectbox("Select anchor bolt size", list(THAI_ANCHOR_BOLTS.keys()), index=2)

        bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]
        d_b = bolt_profile["dia"]

    weld_size_mm = st.slider("Actual fillet weld leg size (mm):", 3, 16, 8)

# ------------------------------------------
# COLUMN 2: INTERACTIVE COORDINATE MATRIX & ALERTS
# ------------------------------------------
with col_matrix:
    st.markdown("<div class='column-title'>🎯 2. Bolt Coordinates & Layout</div>", unsafe_allow_html=True)
    st.caption("Freely edit the X, Y coordinates on the plate. The origin (0,0) is at the center of the steel column.")

    init_x = (bf / 2.0) + 45.0
    init_y = (d / 2.0) + 50.0

    if "active_profile" not in st.session_state or st.session_state["active_profile"] != selected_profile:
        st.session_state["active_profile"] = selected_profile
        st.session_state["grid_data"] = pd.DataFrame({
            "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "X (mm)": [-init_x, init_x, -init_x, init_x, -init_x, init_x],
            "Y (mm)": [init_y, init_y, 0.0, 0.0, -init_y, -init_y]
        })

    if st.button("🤖 Auto-Resize (fix bolt coords + auto-enlarge plate)", use_container_width=True):
        fixed_matrix = st.session_state["grid_data"].copy()
        max_abs_x = 0.0
        max_abs_y = 0.0

        for idx, row in fixed_matrix.iterrows():
            curr_x, curr_y = row["X (mm)"], row["Y (mm)"]
            sign_x = 1.0 if curr_x >= 0 else -1.0
            sign_y = 1.0 if curr_y >= 0 else -1.0

            if abs(curr_x) < init_x: curr_x = init_x * sign_x
            if abs(curr_y) < (d/2.0) + 35.0 and abs(curr_y) > 0.0: curr_y = init_y * sign_y

            fixed_matrix.at[idx, "X (mm)"] = curr_x
            fixed_matrix.at[idx, "Y (mm)"] = curr_y

            max_abs_x = max(max_abs_x, abs(curr_x))
            max_abs_y = max(max_abs_y, abs(curr_y))

        st.session_state["grid_data"] = fixed_matrix

        req_B = (max_abs_x + bolt_profile["min_edge"]) * 2.0
        req_N = (max_abs_y + bolt_profile["min_edge"]) * 2.0

        st.session_state["plate_B"] = float(math.ceil(req_B / 10.0) * 10.0)
        st.session_state["plate_N"] = float(math.ceil(req_N / 10.0) * 10.0)
        st.session_state["plate_version"] += 1

        st.rerun()

    edited_df = st.data_editor(st.session_state["grid_data"], num_rows="dynamic", use_container_width=True)
    st.session_state["grid_data"] = edited_df
    num_bolts = len(edited_df)

    # --- COMPUTATIONAL GEOMETRY ENGINE ---
    geometric_errors = []
    min_s_req = 2.67 * d_b
    min_edge_req = bolt_profile["min_edge"]

    if num_bolts > 0:
        for idx, row in edited_df.iterrows():
            bx, by, bid = row["X (mm)"], row["Y (mm)"], row["Bolt ID"]
            actual_min_edge = min((B / 2.0) - bx, bx - (-B / 2.0), (N / 2.0) - by, by - (-N / 2.0))
            if actual_min_edge < min_edge_req:
                geometric_errors.append(f"❌ <b>{bid}:</b> Plate edge distance too short ({actual_min_edge:.1f} mm < {min_edge_req} mm)")
            if (abs(by) <= (d/2.0) + 35.0) and (abs(bx) <= (bf/2.0) + 35.0):
                geometric_errors.append(f"❌ <b>{bid}:</b> Falls inside the conflict zone — hits the column or too tight for a wrench")

        for i in range(num_bolts):
            for j in range(i + 1, num_bolts):
                b1, b2 = edited_df.iloc[i], edited_df.iloc[j]
                dist = math.sqrt((b1["X (mm)"] - b2["X (mm)"])**2 + (b1["Y (mm)"] - b2["Y (mm)"])**2)
                if dist < min_s_req:
                    geometric_errors.append(f"⚠️ <b>{b1['Bolt ID']}-{b2['Bolt ID']}:</b> Spacing too close ({dist:.1f} mm < {min_s_req:.1f} mm)")

    st.markdown("#### 🚨 Geometry & Distance Checker")
    if geometric_errors:
        st.markdown("<div class='danger-card'>" + "<br>".join(geometric_errors) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='rec-card'>✅ <b>Passes all geometry criteria</b> — no column interference</div>", unsafe_allow_html=True)

# ------------------------------------------
# COLUMN 3: ENGINEERING DASHBOARD & 3D MODEL
# ------------------------------------------
with col_result:
    st.markdown("<div class='column-title'>📊 3. Engineering Summary & 3D Model</div>", unsafe_allow_html=True)

    # --- ENGINEERING MECHANICS CALCULATION ---
    P_u_n, V_u_n, M_u_nmm = p_u_kn * 1000.0, v_u_kn * 1000.0, m_u_knm * 1000000.0

    I_y_group = sum(edited_df["Y (mm)"]**2) if num_bolts > 0 else 1.0

    l_flange = 4.0 * bf
    l_web = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0
    l_total = l_flange + l_web

    weld_stress_axial = (P_u_n / l_total) / 1000.0 if l_total > 0 else 0
    weld_stress_moment = (M_u_nmm / (2.0 * bf * (d - tf))) / 1000.0 if bf > 0 else 0
    weld_stress_shear = (V_u_n / l_web) / 1000.0 if l_web > 0 else 0

    total_demand_flange = weld_stress_axial + weld_stress_moment
    total_demand_web = math.sqrt(weld_stress_axial**2 + weld_stress_shear**2)
    max_weld_demand = max(total_demand_flange, total_demand_web)

    F_exx = 490.0
    weld_cap_per_mm = 0.75 * 0.60 * F_exx * 0.707 * weld_size_mm / 1000.0

    min_weld_req = 5 if tp <= 13 else (6 if tp <= 19 else 8)
    strength_weld_req = max_weld_demand / (0.75 * 0.60 * F_exx * 0.707 / 1000.0)
    final_weld_size = max(min_weld_req, math.ceil(strength_weld_req))

    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0

    e_kern = N / 6.0
    e_edge = N / 2.0
    if P_u_n <= 0:
        bearing_case = "no-compression"
        f_p_min = f_p_max_edge = f_p_peak = 0.0
        Y_bearing = 0.0
        bearing_ok = False
    elif ecc <= e_kern:
        bearing_case = "full"
        q_mean = P_u_n / (B * N)
        f_p_min = q_mean * (1.0 - 6.0 * ecc / N)
        f_p_max_edge = q_mean * (1.0 + 6.0 * ecc / N)
        f_p_peak = f_p_max_edge
        Y_bearing = float(N)
        bearing_ok = f_p_peak <= f_p_max
    elif ecc < e_edge:
        bearing_case = "partial"
        Y_bearing = 1.5 * N - 3.0 * ecc
        f_p_peak = (2.0 * P_u_n) / (B * Y_bearing) if Y_bearing > 0 else f_p_max
        f_p_max_edge = f_p_peak
        f_p_min = 0.0
        bearing_ok = f_p_peak <= f_p_max
    else:
        bearing_case = "uplift"
        Y_bearing = 0.0
        f_p_peak = f_p_max
        f_p_max_edge = f_p_peak
        f_p_min = 0.0
        bearing_ok = False

    bearing_actual = f_p_peak

    m_arm = (N - 0.95 * d) / 2.0
    n_arm = (B - 0.80 * bf) / 2.0
    Fy_plate = 245.0
    t_req = max(m_arm, n_arm) * math.sqrt((2.0 * bearing_actual) / (0.90 * Fy_plate))

    bolt_coords = list(zip(edited_df["X (mm)"].astype(float), edited_df["Y (mm)"].astype(float)))
    bolt_sol = solve_bearing_block_bolts(P_u_n, M_u_nmm, B, N, bolt_coords, f_p_max)
    if bolt_sol["ok"]:
        edited_df["Tension (kN)"] = bolt_sol["tensions"]
    else:
        edited_df["Tension (kN)"] = [0.0] * num_bolts
    tensions = list(edited_df["Tension (kN)"])
    bolt_case = bolt_sol.get("case", "unknown")

    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area"]) / 1000.0
    bolt_v_cap = (0.75 * bolt_profile["F_nv"] * bolt_profile["area"]) / 1000.0
    max_v_actual = v_u_kn / num_bolts if num_bolts > 0 else 0.0

    F_nt_b = bolt_profile["F_nt"]
    F_nv_b = bolt_profile["F_nv"]
    A_b = bolt_profile["area"]
    phi_b = 0.75
    f_rv = (max_v_actual * 1000.0) / A_b if A_b > 0 else 0.0
    F_nt_prime = 1.3 * F_nt_b - (F_nt_b / (phi_b * F_nv_b)) * f_rv
    F_nt_prime = min(F_nt_b, max(0.0, F_nt_prime))
    bolt_t_cap_int = (phi_b * F_nt_prime * A_b) / 1000.0

    # --- 3D INTERACTIVE GRAPHICS ENGINE ---
    fig = go.Figure()
    # Base Plate & Column
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#475569', opacity=0.85, name='Plate'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#1e293b', name='Column'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#1e293b', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#334155', showlegend=False))

    # Welds
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), name='Flange Welds'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[tw/2, tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), name='Web Welds'))
    fig.add_trace(go.Scatter3d(x=[-tw/2, -tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), showlegend=False))

    # Anchor Bolts & Tension Indicators
    for _, row in edited_df.iterrows():
        bx, by, tf_bolt, b_id = row["X (mm)"], row["Y (mm)"], row["Tension (kN)"], row["Bolt ID"]
        bolt_col = '#ef4444' if tf_bolt > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-150, tp+20], mode='lines+markers', marker=dict(size=5, color=bolt_col), line=dict(color=bolt_col, width=5), showlegend=False))
        if tf_bolt > 0:
            z_top = tp + 20 + 30 + (tf_bolt * 1.0)
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[tp+20, z_top], mode='lines', line=dict(color='#b91c1c', width=8), showlegend=False))

    # [NEW 3D ENGINE] 1. Pu Force Vector Arrow (Axial Compression)
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[tp+460, tp+360], mode='lines', line=dict(color='#ef4444', width=8), name='Pu Axial Force'))
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+360], u=[0], v=[0], w=[-45], colorscale=[[0, '#ef4444'], [1, '#ef4444']], showscale=False, sizemode='absolute', sizeref=25, name='Pu Tip'))

    # [NEW 3D ENGINE] 2. Vu Force Vector Arrow (Horizontal Shear)
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[-N/2 - 70, -N/2 - 10], z=[tp+10, tp+10], mode='lines', line=dict(color='#10b981', width=8), name='Vu Shear Force'))
    fig.add_trace(go.Cone(x=[0], y=[-N/2 - 10], z=[tp+10], u=[0], v=[45], w=[0], colorscale=[[0, '#10b981'], [1, '#10b981']], showscale=False, sizemode='absolute', sizeref=25, name='Vu Tip'))

    # [NEW 3D ENGINE] 3. Mu Moment Curved Rotational Vector (Bending Arc)
    arc_x, arc_y, arc_z = [], [], []
    R_mu = 65.0
    for i in range(30):
        ang = -math.pi/3 + (i * 1.3 * math.pi / 29)
        arc_x.append(bf/2 + 25)
        arc_y.append(R_mu * math.sin(ang))
        arc_z.append(tp + 200 + R_mu * math.cos(ang))
    fig.add_trace(go.Scatter3d(x=arc_x, y=arc_y, z=arc_z, mode='lines', line=dict(color='#f59e0b', width=8), name='Mu Bending Moment'))
    fig.add_trace(go.Cone(x=[arc_x[-1]], y=[arc_y[-1]], z=[arc_z[-1]], u=[0], v=[40 * math.cos(-math.pi/3 + 1.3*math.pi)], w=[-40 * math.sin(-math.pi/3 + 1.3*math.pi)], colorscale=[[0, '#f59e0b'], [1, '#f59e0b']], showscale=False, sizemode='absolute', sizeref=25, name='Mu Tip'))

    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.1))), margin=dict(l=0, r=0, b=0, t=0), height=400)
    st.plotly_chart(fig, use_container_width=True)


# =========================================================================
# 3. DETAILED CALCULATION TABS (ย้ายออกนอกคอลัมน์เพื่อให้แสดงผล Full-Width)
# =========================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📝 รายการคำนวณอย่างละเอียด (Detailed Calculation Reports)")

tab_weld, tab_plate, tab_bolt = st.tabs(["🔥 1. Welds Calculation", "🔲 2. Base Plate Design", "🔩 3. Anchor Bolts Check"])

# ---------------- TAB 1: WELD ----------------
with tab_weld:
    st.info(f"**Analysis assumptions:** Elastic Line Method | E70XX electrodes | Actual weld size = **{weld_size_mm} mm**")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Analyze force demand on the weld (Demand)")
        st.caption(f"Flange weld length ($L_f$) = {l_flange:.0f} mm | Web weld length ($L_w$) = {l_web:.0f} mm")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"- **Axial stress:** $f_a = \\frac{{P_u}}{{L_f + L_w}} = {weld_stress_axial:.2f}$ kN/mm")
            st.markdown(f"- **Bending stress (flange):** $f_m = \\frac{{M_u}}{{2 b_f (d - t_f)}} = {weld_stress_moment:.2f}$ kN/mm")
        with c2:
            st.markdown(f"- **Shear stress (web):** $f_v = \\frac{{V_u}}{{L_w}} = {weld_stress_shear:.2f}$ kN/mm")

        st.divider()
        st.markdown(f"""
        **Critical resultant demand (Maximum Resultant Demand):**
        - Flange (axial + bending): $f_{{req,f}} = f_a + f_m =$ **{total_demand_flange:.2f} kN/mm**
        - Web (axial + shear): $f_{{req,w}} = \\sqrt{{f_a^2 + f_v^2}} =$ **{total_demand_web:.2f} kN/mm**
        """)

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Weld capacity (Capacity)")
        st.markdown(f"$$ \\phi R_n = 0.75 \\times 0.60 \\times F_{{EXX}} \\times 0.707 \\times a $$")
        st.markdown(f"$$ \\phi R_n = 0.75 \\times 0.60 \\times 490 \\times 0.707 \\times ({weld_size_mm} / 1000) = {weld_cap_per_mm:.2f} \\text{{ kN/mm}} $$")

    with st.container(border=True):
        st.markdown("##### 📌 Step 3: Recommended weld size (Sizing)")
        st.markdown(f"- **Constructability minimum** (by plate thickness): **{min_weld_req} mm**")
        st.markdown(f"- **Strength requirement** ($a_{{strength}} = f_{{req}} / \\phi R_{{n,per\\,mm}}$): **{strength_weld_req:.2f} mm**")
        st.markdown(f"$$ a_{{req}} = \\max({min_weld_req},\\; \\lceil {strength_weld_req:.2f} \\rceil) = \\textbf{{{final_weld_size} mm}} $$")
        if weld_size_mm >= final_weld_size:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✔️ **Actual weld size ({weld_size_mm} mm) ≥ recommended ({final_weld_size} mm)**")
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;⚠️ **Actual weld size ({weld_size_mm} mm) < recommended ({final_weld_size} mm) — size up**")

    if max_weld_demand <= weld_cap_per_mm:
        st.markdown(f"<div class='rec-card'>✅ <b>PASS:</b> Max demand <b>{max_weld_demand:.2f} kN/mm</b> $\\le$ Capacity <b>{weld_cap_per_mm:.2f} kN/mm</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='danger-card'>❌ <b>FAIL:</b> Max demand <b>{max_weld_demand:.2f} kN/mm</b> > Capacity <b>{weld_cap_per_mm:.2f} kN/mm</b> (please increase the weld size)</div>", unsafe_allow_html=True)

# ---------------- TAB 2: PLATE ----------------
with tab_plate:
    st.info(f"**Analysis assumptions:** AISC Design Guide 1 | SS400 plate steel (Yield Strength = **{Fy_plate:.0f} MPa**)")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Check concrete bearing pressure (Bearing Pressure)")
        st.markdown(f"Load eccentricity $e = M_u/P_u = {ecc:.1f}$ mm  |  Kern $= N/6 = {e_kern:.1f}$ mm  |  Edge $= N/2 = {e_edge:.1f}$ mm")

        regime_map = {
            "no-compression": ("⚠️ No axial compression — bearing cannot form; bolts/uplift govern (#4).", "danger"),
            "full":           ("ℹ️ Full contact: trapezoidal pressure over the whole plate ($e \\le N/6$).", "info"),
            "partial":        ("ℹ️ Partial contact: triangular pressure over length $Y$ from the compression edge ($N/6 < e < N/2$).", "info"),
            "uplift":         ("⚠️ Resultant outside the plate ($e \\ge N/2$): bearing alone cannot equilibrate — bolts must anchor the uplift.", "danger"),
        }
        banner_text, banner_kind = regime_map.get(bearing_case, ("Unknown bearing case.", "danger"))
        banner_cls = "rec-card" if banner_kind == "info" else "danger-card"
        st.markdown(f"<div class='{banner_cls}'>{banner_text}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Peak bearing pressure (Actual):**")
            if bearing_case == "full":
                st.markdown(f"$$ f_{{p,max}} = \\frac{{P_u}}{{BN}}\\left(1 + \\frac{{6e}}{{N}}\\right) = {f_p_peak:.2f} \\text{{ MPa}} $$")
                st.caption(f"Tension-side edge: $f_{{p,min}} = {f_p_min:.2f}$ MPa")
            elif bearing_case == "partial":
                st.markdown(f"$Y = 1.5N - 3e = 1.5({N:.0f}) - 3({ecc:.0f}) = $ **{Y_bearing:.1f} mm** (bearing length)")
                st.markdown(f"$$ f_{{p,peak}} = \\frac{{2P_u}}{{B \\cdot Y}} = {f_p_peak:.2f} \\text{{ MPa}} $$")
            else:
                st.markdown(f"$$ f_{{p,peak}} = {f_p_peak:.2f} \\text{{ MPa}} \\; (\\text{{capacity used as governing value}}) $$")
        with c2:
            st.markdown("**Max bearing capacity (Capacity):**")
            st.markdown(f"$$ \\phi_c f_{{p,max}} = 0.65 (0.85 f_c') = {f_p_max:.2f} \\text{{ MPa}} $$")

        if bearing_ok:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✔️ **Status:** Concrete bearing is adequate ($f_{{p,peak}} = {f_p_peak:.2f} \\le \\phi_c f_{{p,max}} = {f_p_max:.2f}$)")
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;❌ **Status:** Concrete bearing exceeded — enlarge the plate (B, N) or increase $f'_c$")

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Calculate required plate thickness (Required Thickness)")
        st.markdown(f"- Y-direction cantilever ($m$) = $({N} - 0.95({d})) / 2 = {m_arm:.1f}$ mm")
        st.markdown(f"- X-direction cantilever ($n$) = $({B} - 0.80({bf})) / 2 = {n_arm:.1f}$ mm")

        l_crit = max(m_arm, n_arm)
        st.markdown(f"**Critical distance ($l$) = $\\max(m, n) = {l_crit:.1f}$ mm**")
        st.markdown(f"$$ t_{{req}} = l \\sqrt{{\\frac{{2 f_p}}{{0.90 F_y}}}} = {l_crit:.1f} \\sqrt{{\\frac{{2({bearing_actual:.2f})}}{{0.90({Fy_plate})}}}} = {t_req:.2f} \\text{{ mm}} $$")

    if t_req <= tp:
        st.markdown(f"<div class='rec-card'>✅ <b>PASS:</b> Required thickness <b>{t_req:.2f} mm</b> $\\le$ Actual thickness <b>{tp} mm</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='danger-card'>❌ <b>FAIL:</b> Required thickness <b>{t_req:.2f} mm</b> > Actual thickness <b>{tp} mm</b> (please increase the plate thickness)</div>", unsafe_allow_html=True)

# ---------------- TAB 3: BOLT ----------------
with tab_bolt:
    st.info(f"**Analysis method:** Bearing-block equilibrium (AISC Design Guide 1) | Bolts **{bolt_name}** | Number of bolts = **{num_bolts}**")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Force distribution to the bolts (Bolt Demands)")
        bolt_group_I_label = f"Bolt-group moment of inertia about the X-axis ($I_y$) = **{I_y_group:,.0f} mm²** (reference only)"

        if bolt_case == "bearing-only":
            st.markdown(bolt_group_I_label)
            st.markdown(
                "Bearing alone equilibrates both $P_u$ and $M_u$ "
                "($e = M_u/P_u \\le N/2$), so **all bolts take zero tension** — they resist shear only."
            )
            st.markdown(f"$$ T_{{u,max}} = 0.00 \\text{{ kN}} \\qquad V_{{u,bolt}} = \\frac{{V_u}}{{N_{{bolt}}}} = {max_v_actual:.2f} \\text{{ kN}} $$")

        elif bolt_case == "uplift" and bolt_sol["ok"]:
            Y_b = bolt_sol["Y"]; C_b = bolt_sol["C"]; k_b = bolt_sol["k"]
            y_NA_b = bolt_sol["y_NA"]; T_tot = bolt_sol["total_T_kN"]
            st.markdown(
                "Bearing alone **cannot** equilibrate the load ($e > N/2$). A uniform bearing block "
                f"of stress $\\phi_c 0.85 f'_c = {f_p_max:.2f}$ MPa forms over length $Y$ at the "
                "compression edge, and the bolts above the neutral axis resist the net tension "
                "elastically (force proportional to distance above $y_{NA}$)."
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Bearing block:**")
                st.markdown(f"$Y = $ **{Y_b:.1f} mm** &nbsp;→&nbsp; $y_{{NA}} = -N/2 + Y = $ **{y_NA_b:.1f} mm**")
                st.markdown(f"$C = q_{{max}} B Y = $ **{C_b/1000.0:.1f} kN**")
            with c2:
                st.markdown("**Bolt tensions:**")
                st.markdown(f"$T_i = k(y_i - y_{{NA}})$, &nbsp; $k = $ **{k_b:.1f} N/mm**")
                st.markdown(f"$\\Sigma T = $ **{T_tot:.1f} kN** &nbsp;←&nbsp; checks $C - P_u = {(C_b-P_u_n)/1000.0:.1f}$ kN")

            tbl = edited_df[["Bolt ID", "Y (mm)", "Tension (kN)"]].copy()
            tbl["Y (mm)"] = tbl["Y (mm)"].map("{:.0f}".format)
            tbl["Tension (kN)"] = tbl["Tension (kN)"].map("{:.2f}".format)
            st.dataframe(tbl, use_container_width=True, hide_index=True)

            st.markdown(
                f"**Critical tension:** $T_{{u,max}} = $ **{max_t_actual:.2f} kN** &nbsp;|&nbsp; "
                f"**Shear per bolt:** $V_{{u,bolt}} = V_u/N_{{bolt}} = $ **{max_v_actual:.2f} kN**"
            )
            st.caption(f"Equilibrium check: ΣF residual = {bolt_sol['resid_F']:.2e} N, ΣM residual = {bolt_sol['resid_M']:.2e} N·mm (≈0 confirms consistency)")

        else:
            st.markdown(bolt_group_I_label)
            st.markdown(f"<div class='danger-card'>⚠️ <b>Bearing-block solver:</b> {bolt_sol.get('reason','could not converge')} — bolt tensions not available; revise the connection.</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Bolt capacities (Bolt Capacities)")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Tension capacity ($T_{{cap}}$):**")
            st.markdown(f"$$ \\phi R_{{nt}} = 0.75 F_{{nt}} A_b = {bolt_t_cap:.2f} \\text{{ kN}} $$")
        with c2:
            st.markdown("**Shear capacity ($V_{{cap}}$):**")
            st.markdown(f"$$ \\phi R_{{nv}} = 0.75 F_{{nv}} A_b = {bolt_v_cap:.2f} \\text{{ kN}} $$")

    with st.container(border=True):
        st.markdown("##### 📌 Step 3: Combined tension + shear interaction (AISC J3.7)")
        st.caption("When a bolt resists both tension and shear at the same time, its tensile capacity is reduced.")
        st.markdown(f"Required shear stress $f_{{rv}} = V_{{u,bolt}}/A_b = {max_v_actual*1000.0:.0f}/{A_b:.0f} = $ **{f_rv:.1f} MPa**")
        st.markdown(f"$$ F'_{{nt}} = 1.3 F_{{nt}} - \\frac{{F_{{nt}}}}{{\\phi F_{{nv}}}} f_{{rv}} = 1.3({F_nt_b:.0f}) - \\frac{{{F_nt_b:.0f}}}{{0.75({F_nv_b:.0f})}}({f_rv:.1f}) = {F_nt_prime:.1f} \\text{{ MPa}} \\le F_{{nt}} $$")
        st.markdown(f"**Reduced tension capacity:** $\\phi R'_{{nt}} = 0.75 F'_{{nt}} A_b = $ **{bolt_t_cap_int:.2f} kN**")
        st.markdown(f"Critical tension demand $T_{{u,max}} =$ **{max_t_actual:.2f} kN** → "
                    f"($T_{{u,max}} / \\phi R'_{{nt}} =$ **{max_t_actual/bolt_t_cap_int:.2f}**)")

    t_pass = max_t_actual <= bolt_t_cap_int
    v_pass = max_v_actual <= bolt_v_cap

    if t_pass and v_pass:
        st.markdown(f"<div class='rec-card'>✅ <b>PASS:</b> Bolts safely resist combined tension, shear, and their interaction per AISC J3.7</div>", unsafe_allow_html=True)
    else:
        errors = []
        if not t_pass: errors.append(f"Critical tension ({max_t_actual:.2f} kN) > Reduced capacity φR'nt ({bolt_t_cap_int:.2f} kN)")
        if not v_pass: errors.append(f"Shear ({max_v_actual:.2f} kN) > Capacity φRnv ({bolt_v_cap:.2f} kN)")
        error_text = "<br>".join([f"- {e}" for e in errors])

        st.markdown(f"<div class='danger-card'>❌ <b>FAIL: Bolts cannot resist the loads</b><br>{error_text}</div>", unsafe_allow_html=True)
