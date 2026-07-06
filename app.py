# app.py
"""
AISC Steel-Connection Ultimate Engine — Streamlit front end.

This module is UI orchestration only. All engineering math lives in
calculations.py (pure functions) and the lookup tables live in
constants.py. Keeping the split this way means the calculations can be
unit-tested (see tests/test_calculations.py) without spinning up Streamlit.
"""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import (
    bolt_steel_capacities,
    check_bolt_geometry,
    check_concrete_capacities,
    compute_bearing_regime,
    default_bolt_layout,
    default_plate_size,
    design_perimeter_weld,
    plate_thickness_compression_side,
    plate_thickness_tension_side,
    solve_bearing_block_bolts,
)
from constants import (
    STEEL_PLATE_GRADES,
    THAI_ANCHOR_BOLTS,
    THAI_H_BEAM_PROFILES,
    THAI_PLATE_THICKNESSES,
    WELD_ELECTRODE_GRADES,
)

# ==========================================
# Page config & styling
# ==========================================
st.set_page_config(page_title="AISC Ultra-Matrix Connection Engine", layout="wide")

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
st.markdown(
    "<div class='sub-title'>Independent bolt-group coordinate engine with edge-distance checks, "
    "steel-interference checks, and weld force distribution per AISC LRFD</div>",
    unsafe_allow_html=True,
)


def reset_layout_for_profile(prof: dict) -> None:
    """(Re)initialize plate size and bolt grid session state for a column profile."""
    B, N = default_plate_size(prof["bf"], prof["d"])
    st.session_state["plate_B"] = B
    st.session_state["plate_N"] = N
    st.session_state["grid_data"] = pd.DataFrame(default_bolt_layout(prof["bf"], prof["d"]))


# ==========================================
# 3-column studio layout
# ==========================================
col_input, col_matrix, col_result = st.columns([0.9, 1.0, 1.1])

# ------------------------------------------
# COLUMN 1: Structural input parameters
# ------------------------------------------
with col_input:
    st.markdown("<div class='column-title'>🎛️ 1. Connection Section & Factored Loads</div>", unsafe_allow_html=True)

    selected_profile = st.selectbox("Connected steel column section (H-Beam TIS):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
    prof = THAI_H_BEAM_PROFILES[selected_profile]

    if "active_profile" not in st.session_state:
        st.session_state["active_profile"] = selected_profile
        st.session_state["plate_version"] = 0
        reset_layout_for_profile(prof)

    if st.session_state["active_profile"] != selected_profile:
        st.session_state["active_profile"] = selected_profile
        st.session_state["plate_version"] += 1
        reset_layout_for_profile(prof)
        st.rerun()

    with st.container(border=True):
        st.caption("📐 Steel section dimensions (mm)")
        c1, c2 = st.columns(2)
        d = c1.number_input("Depth d", value=prof["d"], min_value=50.0, step=1.0)
        bf = c2.number_input("Flange width bf", value=prof["bf"], min_value=50.0, step=1.0)
        tw = c1.number_input("Web thickness tw", value=prof["tw"], min_value=1.0, step=0.5)
        tf = c2.number_input("Flange thickness tf", value=prof["tf"], min_value=1.0, step=0.5)

    with st.container(border=True):
        st.caption("🏗️ Material Properties (เกรดวัสดุ)")
        cx_m1, cx_m2 = st.columns(2)

        selected_plate_grade = cx_m1.selectbox("Base Plate Grade (เกรดเหล็ก):", list(STEEL_PLATE_GRADES.keys()), index=0)
        Fy_plate = STEEL_PLATE_GRADES[selected_plate_grade]["Fy"]

        selected_weld_grade = cx_m2.selectbox("Weld Electrode (เกรดลวดเชื่อม):", list(WELD_ELECTRODE_GRADES.keys()), index=0)
        F_exx = WELD_ELECTRODE_GRADES[selected_weld_grade]["F_exx"]

    with st.container(border=True):
        st.caption("⚡ Factored loads & Concrete info")
        cx1, cx2 = st.columns(2)
        p_u_kn = cx1.number_input("Axial comp. Pu (kN)", value=500.0, min_value=0.0)
        v_u_kn = cx2.number_input("Shear Vu (kN)", value=100.0, min_value=0.0)
        m_u_knm = cx1.number_input("Moment Mu (kN-m)", value=140.0, min_value=0.0)
        fc_mpa = cx2.number_input("Concrete f'c (MPa)", value=28.0, min_value=1.0)

        h_ef = cx1.number_input("Embedment Depth h_ef (mm)", value=250.0, min_value=50.0)
        c_edge = cx2.number_input("Concrete Edge c_a1 (mm)", value=200.0, min_value=10.0)

    with st.container(border=True):
        st.caption("🔩 Base plate and anchor bolt sizes")
        B = st.number_input(
            "Plate width B (mm)", value=st.session_state["plate_B"], min_value=100.0,
            key=f"B_{st.session_state['plate_version']}",
        )
        N = st.number_input(
            "Plate length N (mm)", value=st.session_state["plate_N"], min_value=100.0,
            key=f"N_{st.session_state['plate_version']}",
        )

        tp = st.selectbox("Plate thickness tp (mm)", THAI_PLATE_THICKNESSES, index=3)
        bolt_name = st.selectbox("Select anchor bolt size", list(THAI_ANCHOR_BOLTS.keys()), index=2)

        bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]
        d_b = bolt_profile["dia"]

    weld_size_mm = st.slider("Actual fillet weld leg size (mm):", 3, 16, 8)

# ------------------------------------------
# COLUMN 2: Interactive coordinate matrix & geometry alerts
# ------------------------------------------
with col_matrix:
    st.markdown("<div class='column-title'>🎯 2. Bolt Coordinates & Layout</div>", unsafe_allow_html=True)
    st.caption("Freely edit the X, Y coordinates on the plate. The origin (0,0) is at the center of the steel column.")

    if st.button("🤖 Auto-Resize (fix bolt coords + auto-enlarge plate)", use_container_width=True):
        fixed_matrix = st.session_state["grid_data"].copy()
        max_abs_x = 0.0
        max_abs_y = 0.0
        init_x, init_y = (bf / 2.0) + 45.0, (d / 2.0) + 50.0

        for idx, row in fixed_matrix.iterrows():
            curr_x, curr_y = row["X (mm)"], row["Y (mm)"]
            sign_x = 1.0 if curr_x >= 0 else -1.0
            sign_y = 1.0 if curr_y >= 0 else -1.0

            if abs(curr_x) < init_x:
                curr_x = init_x * sign_x
            if abs(curr_y) < (d / 2.0) + 35.0 and abs(curr_y) > 0.0:
                curr_y = init_y * sign_y

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

    # Explicit key tied to plate_version: without this, Streamlit's
    # data_editor keeps its own internal widget state after the first
    # render and silently ignores programmatic updates to grid_data made
    # by "Auto-Resize" or a column-profile change (a real bug in the
    # original app — the editor could visually go stale after those
    # actions). Bumping plate_version remounts the widget with fresh data.
    edited_df = st.data_editor(
        st.session_state["grid_data"],
        num_rows="dynamic",
        use_container_width=True,
        key=f"bolt_grid_{st.session_state['plate_version']}",
    )
    st.session_state["grid_data"] = edited_df
    num_bolts = len(edited_df)

    if num_bolts == 0:
        st.error("❌ ข้อมูลขัดข้อง: ต้องมี Anchor Bolt อย่างน้อย 1 ตัวในระบบเพื่อทำการคำนวณ โปรดเพิ่มโบลต์เพื่อดำเนินการต่อ")
        st.stop()

    min_s_req = 2.67 * d_b
    min_edge_req = bolt_profile["min_edge"]
    bolts_for_check = [
        (row["Bolt ID"], row["X (mm)"], row["Y (mm)"])
        for _, row in edited_df.iterrows()
    ]
    geometric_errors = check_bolt_geometry(bolts_for_check, B, N, bf, d, min_edge_req, min_s_req)

    st.markdown("#### 🚨 Geometry & Distance Checker")
    if geometric_errors:
        st.markdown("<div class='danger-card'>" + "<br>".join(geometric_errors) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='rec-card'>✅ <b>Passes all geometry criteria</b> — no column interference</div>", unsafe_allow_html=True)

# ------------------------------------------
# COLUMN 3: Engineering dashboard & 3D model
# ------------------------------------------
with col_result:
    st.markdown("<div class='column-title'>📊 3. Engineering Summary & 3D Model</div>", unsafe_allow_html=True)

    P_u_n, V_u_n, M_u_nmm = p_u_kn * 1000.0, v_u_kn * 1000.0, m_u_knm * 1_000_000.0

    I_x_group = float((edited_df["Y (mm)"] ** 2).sum()) if num_bolts > 0 else 1.0

    weld_res = design_perimeter_weld(P_u_n, V_u_n, M_u_nmm, d, bf, tf, weld_size_mm, F_exx, tp)

    bearing = compute_bearing_regime(P_u_n, M_u_nmm, B, N, fc_mpa)
    f_p_max = bearing.f_p_max_capacity
    bearing_actual = bearing.f_p_peak

    m_arm, n_arm, t_req_compression = plate_thickness_compression_side(N, d, B, bf, bearing_actual, Fy_plate)

    bolt_coords = list(zip(edited_df["X (mm)"].astype(float), edited_df["Y (mm)"].astype(float)))
    bolt_sol = solve_bearing_block_bolts(P_u_n, M_u_nmm, B, N, bolt_coords, f_p_max)
    edited_df["Tension (kN)"] = bolt_sol.tensions if bolt_sol.ok else [0.0] * num_bolts
    tensions = list(edited_df["Tension (kN)"])
    bolt_case = bolt_sol.case

    tension_and_y = list(zip(edited_df["Tension (kN)"], edited_df["Y (mm)"]))
    max_t_actual, f_arm, b_eff, t_req_tension = plate_thickness_tension_side(tension_and_y, d, B, Fy_plate)

    t_req = max(t_req_compression, t_req_tension)

    bolt_cap = bolt_steel_capacities(bolt_profile["F_nt"], bolt_profile["F_nv"], bolt_profile["area"], v_u_kn, num_bolts)
    bolt_t_cap = bolt_cap.tension_capacity_kN
    bolt_v_cap = bolt_cap.shear_capacity_kN
    max_v_actual = bolt_cap.shear_per_bolt_kN
    f_rv = bolt_cap.f_rv
    F_nt_prime = bolt_cap.F_nt_prime
    bolt_t_cap_int = bolt_cap.tension_capacity_with_shear_kN

    # --- 3D interactive graphics ---
    fig = go.Figure()

    cz_x = bf / 2.0 + 35.0
    cz_y = d / 2.0 + 35.0
    fig.add_trace(go.Mesh3d(
        x=[-cz_x, cz_x, cz_x, -cz_x, -cz_x, cz_x, cz_x, -cz_x],
        y=[-cz_y, -cz_y, cz_y, cz_y, -cz_y, -cz_y, cz_y, cz_y],
        z=[tp, tp, tp, tp, tp + 150, tp + 150, tp + 150, tp + 150],
        color='#ef4444', opacity=0.15, name='Conflict Zone', hoverinfo='skip',
    ))

    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#475569', opacity=0.85, name='Plate'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#1e293b', name='Column'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#1e293b', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+350, tp+350, tp+350, tp+350], color='#334155', showlegend=False))

    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), name='Flange Welds'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[tw/2, tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), name='Web Welds'))
    fig.add_trace(go.Scatter3d(x=[-tw/2, -tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), showlegend=False))

    for _, row in edited_df.iterrows():
        bx, by, tf_bolt, b_id = row["X (mm)"], row["Y (mm)"], row["Tension (kN)"], row["Bolt ID"]
        bolt_col = '#ef4444' if tf_bolt > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-150, tp+20], mode='lines+markers', marker=dict(size=5, color=bolt_col), line=dict(color=bolt_col, width=5), showlegend=False))
        if tf_bolt > 0:
            z_top = tp + 20 + 30 + (tf_bolt * 1.0)
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[tp+20, z_top], mode='lines', line=dict(color='#b91c1c', width=8), showlegend=False))

    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[tp+460, tp+360], mode='lines', line=dict(color='#ef4444', width=8), name='Pu Axial Force'))
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+360], u=[0], v=[0], w=[-45], colorscale=[[0, '#ef4444'], [1, '#ef4444']], showscale=False, sizemode='absolute', sizeref=25, name='Pu Tip'))

    fig.add_trace(go.Scatter3d(x=[0, 0], y=[-N/2 - 70, -N/2 - 10], z=[tp+10, tp+10], mode='lines', line=dict(color='#10b981', width=8), name='Vu Shear Force'))
    fig.add_trace(go.Cone(x=[0], y=[-N/2 - 10], z=[tp+10], u=[0], v=[45], w=[0], colorscale=[[0, '#10b981'], [1, '#10b981']], showscale=False, sizemode='absolute', sizeref=25, name='Vu Tip'))

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
# Detailed calculation tabs
# =========================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📝 รายการคำนวณอย่างละเอียด (Detailed Calculation Reports)")

tab_weld, tab_plate, tab_bolt = st.tabs(["🔥 1. Welds Calculation", "🔲 2. Base Plate Design", "🔩 3. Anchor Bolts Check"])

# ---------------- TAB 1: WELD ----------------
with tab_weld:
    st.info(f"**Analysis assumptions:** Elastic Line Method | **{selected_weld_grade}** | Actual weld size = **{weld_size_mm} mm**")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Analyze force demand on the weld (Demand)")
        st.caption(f"Flange weld length ($L_f$) = {weld_res.l_flange:.0f} mm | Web weld length ($L_w$) = {weld_res.l_web:.0f} mm")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"- **Axial stress:** $f_a = \\frac{{P_u}}{{L_f + L_w}} = {weld_res.stress_axial:.2f}$ kN/mm")
            st.markdown(f"- **Bending stress (flange):** $f_m = \\frac{{M_u}}{{2 b_f (d - t_f)}} = {weld_res.stress_moment:.2f}$ kN/mm")
        with c2:
            st.markdown(f"- **Shear stress (web):** $f_v = \\frac{{V_u}}{{L_w}} = {weld_res.stress_shear:.2f}$ kN/mm")

        st.divider()
        st.markdown(f"""
        **Critical resultant demand (Maximum Resultant Demand):**
        - Flange (axial + bending): $f_{{req,f}} = f_a + f_m =$ **{weld_res.demand_flange:.2f} kN/mm**
        - Web (axial + shear): $f_{{req,w}} = \\sqrt{{f_a^2 + f_v^2}} =$ **{weld_res.demand_web:.2f} kN/mm**
        """)

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Weld capacity (Capacity)")
        st.markdown(f"$$ \\phi R_n = 0.75 \\times 0.60 \\times F_{{EXX}} \\times 0.707 \\times a $$")
        st.markdown(f"$$ \\phi R_n = 0.75 \\times 0.60 \\times {F_exx:.0f} \\times 0.707 \\times ({weld_size_mm} / 1000) = {weld_res.capacity_per_mm:.2f} \\text{{ kN/mm}} $$")

    with st.container(border=True):
        st.markdown("##### 📌 Step 3: Recommended weld size (Sizing)")
        st.markdown(f"- **Constructability minimum** (by plate thickness): **{weld_res.min_size_constructability} mm**")
        st.markdown(f"- **Strength requirement** ($a_{{strength}} = f_{{req}} / \\phi R_{{n,per\\,mm}}$): **{weld_res.strength_required_size:.2f} mm**")
        st.markdown(f"$$ a_{{req}} = \\max({weld_res.min_size_constructability},\\; \\lceil {weld_res.strength_required_size:.2f} \\rceil) = \\textbf{{{weld_res.recommended_size} mm}} $$")
        if weld_size_mm >= weld_res.recommended_size:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✔️ **Actual weld size ({weld_size_mm} mm) ≥ recommended ({weld_res.recommended_size} mm)**")
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;⚠️ **Actual weld size ({weld_size_mm} mm) < recommended ({weld_res.recommended_size} mm) — size up**")

    if weld_res.passes:
        st.markdown(f"<div class='rec-card'>✅ <b>PASS:</b> Max demand <b>{weld_res.max_demand:.2f} kN/mm</b> $\\le$ Capacity <b>{weld_res.capacity_per_mm:.2f} kN/mm</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='danger-card'>❌ <b>FAIL:</b> Max demand <b>{weld_res.max_demand:.2f} kN/mm</b> > Capacity <b>{weld_res.capacity_per_mm:.2f} kN/mm</b> (please increase the weld size)</div>", unsafe_allow_html=True)

# ---------------- TAB 2: PLATE ----------------
with tab_plate:
    st.info(f"**Analysis assumptions:** AISC Design Guide 1 | **{selected_plate_grade}**")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Check concrete bearing pressure (Bearing Pressure)")
        st.markdown(f"Load eccentricity $e = M_u/P_u = {bearing.eccentricity:.1f}$ mm  |  Kern $= N/6 = {bearing.e_kern:.1f}$ mm  |  Edge $= N/2 = {bearing.e_edge:.1f}$ mm")

        regime_map = {
            "no-compression": ("⚠️ No axial compression — bearing cannot form; bolts/uplift govern (#4).", "danger"),
            "full":           ("ℹ️ Full contact: trapezoidal pressure over the whole plate ($e \\le N/6$).", "info"),
            "partial":        ("ℹ️ Partial contact: triangular pressure over length $Y$ from the compression edge ($N/6 < e < N/2$).", "info"),
            "uplift":         ("⚠️ Resultant outside the plate ($e \\ge N/2$): bearing alone cannot equilibrate — bolts must anchor the uplift.", "danger"),
        }
        banner_text, banner_kind = regime_map.get(bearing.case, ("Unknown bearing case.", "danger"))
        banner_cls = "rec-card" if banner_kind == "info" else "danger-card"
        st.markdown(f"<div class='{banner_cls}'>{banner_text}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Peak bearing pressure (Actual):**")
            if bearing.case == "full":
                st.markdown(f"$$ f_{{p,max}} = \\frac{{P_u}}{{BN}}\\left(1 + \\frac{{6e}}{{N}}\\right) = {bearing.f_p_peak:.2f} \\text{{ MPa}} $$")
                st.caption(f"Tension-side edge: $f_{{p,min}} = {bearing.f_p_min:.2f}$ MPa")
            elif bearing.case == "partial":
                st.markdown(f"$Y = 1.5N - 3e = 1.5({N:.0f}) - 3({bearing.eccentricity:.0f}) = $ **{bearing.Y_bearing:.1f} mm** (bearing length)")
                st.markdown(f"$$ f_{{p,peak}} = \\frac{{2P_u}}{{B \\cdot Y}} = {bearing.f_p_peak:.2f} \\text{{ MPa}} $$")
            else:
                st.markdown(f"$$ f_{{p,peak}} = {bearing.f_p_peak:.2f} \\text{{ MPa}} \\; (\\text{{capacity used as governing value}}) $$")
        with c2:
            st.markdown("**Max bearing capacity (Capacity):**")
            st.markdown(f"$$ \\phi_c f_{{p,max}} = 0.65 (0.85 f_c') = {f_p_max:.2f} \\text{{ MPa}} $$")

        if bearing.ok:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✔️ **Status:** Concrete bearing is adequate ($f_{{p,peak}} = {bearing.f_p_peak:.2f} \\le \\phi_c f_{{p,max}} = {f_p_max:.2f}$)")
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;❌ **Status:** Concrete bearing exceeded — enlarge the plate (B, N) or increase $f'_c$")

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Calculate required plate thickness (Required Thickness)")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🔹 ฝั่งรับแรงกด (Compression Side Check):**")
            st.markdown(f"- ระยะยื่น Cantilever ($m$) = {m_arm:.1f} mm")
            st.markdown(f"- ระยะยื่น Cantilever ($n$) = {n_arm:.1f} mm")
            st.markdown(f"$$ t_{{req,comp}} = \\max(m,n) \\sqrt{{\\frac{{2 f_p}}{{0.90 F_y}}}} = {t_req_compression:.2f} \\text{{ mm}} $$")

        with c2:
            st.markdown("**🔸 ฝั่งรับแรงดึง (Tension Side Check):**")
            if max_t_actual > 0 and f_arm > 0:
                st.markdown(f"- แรงดึงวิกฤตสลักเกลียว ($T_{{u,max}}$) = {max_t_actual:.2f} kN")
                st.markdown(f"- ระยะงัดถึงปีกเสา ($f_{{arm}}$) = {f_arm:.1f} mm")
                st.markdown(f"- ความกว้างประสิทธิผล ($b_{{eff}}$) = {b_eff:.1f} mm")
                st.markdown(f"$$ t_{{req,tens}} = \\sqrt{{\\frac{{4 (T_{{u,max}} \\cdot f_{{arm}})}}{{0.90 F_y b_{{eff}}}}}} = {t_req_tension:.2f} \\text{{ mm}} $$")
            else:
                st.markdown("<div style='color: gray; padding-top: 10px;'>ไม่มีแรงดึงเกิดขึ้นในสลักเกลียว หรือไม่มีโบลต์อยู่นอกแนวปีกเสา (ไม่ต้องคำนวณหนาฝั่งดึง)</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown(f"**สรุปความหนาที่ควบคุมการออกแบบ:** $t_{{req}} = \\max({t_req_compression:.2f}, {t_req_tension:.2f}) = \\textbf{{{t_req:.2f} mm}}$")

    if t_req <= tp:
        st.markdown(f"<div class='rec-card'>✅ <b>PASS:</b> Required thickness <b>{t_req:.2f} mm</b> $\\le$ Actual thickness <b>{tp} mm</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='danger-card'>❌ <b>FAIL:</b> Required thickness <b>{t_req:.2f} mm</b> > Actual thickness <b>{tp} mm</b> (please increase the plate thickness)</div>", unsafe_allow_html=True)

# ---------------- TAB 3: BOLT ----------------
with tab_bolt:
    st.info(f"**Analysis method:** Bearing-block equilibrium (AISC Design Guide 1) | Bolts **{bolt_name}** | Number of bolts = **{num_bolts}**")

    with st.container(border=True):
        st.markdown("##### 📌 Step 1: Force distribution to the bolts (Bolt Demands)")
        bolt_group_I_label = f"Bolt-group moment of inertia about the X-axis ($I_x$) = **{I_x_group:,.0f} mm²** (reference only)"

        if bolt_case == "bearing-only":
            st.markdown(bolt_group_I_label)
            st.markdown(
                "Bearing alone equilibrates both $P_u$ and $M_u$ "
                "($e = M_u/P_u \\le N/2$), so **all bolts take zero tension** — they resist shear only."
            )
            st.markdown(f"$$ T_{{u,max}} = 0.00 \\text{{ kN}} \\qquad V_{{u,bolt}} = \\frac{{V_u}}{{N_{{bolt}}}} = {max_v_actual:.2f} \\text{{ kN}} $$")

        elif bolt_case == "uplift" and bolt_sol.ok:
            Y_b, C_b, k_b = bolt_sol.Y, bolt_sol.C, bolt_sol.k
            y_NA_b, T_tot = bolt_sol.y_NA, bolt_sol.total_T_kN
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
            st.caption(f"Equilibrium check: ΣF residual = {bolt_sol.resid_F:.2e} N, ΣM residual = {bolt_sol.resid_M:.2e} N·mm (≈0 confirms consistency)")

        else:
            st.markdown(bolt_group_I_label)
            st.markdown(f"<div class='danger-card'>⚠️ <b>Bearing-block solver:</b> {bolt_sol.reason or 'could not converge'} — bolt tensions not available; revise the connection.</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("##### 📌 Step 2: Bolt capacities (Steel Bolt Capacities)")

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
        st.markdown(f"Required shear stress $f_{{rv}} = V_{{u,bolt}}/A_b = {max_v_actual*1000.0:.0f}/{bolt_profile['area']:.0f} = $ **{f_rv:.1f} MPa**")
        st.markdown(f"$$ F'_{{nt}} = 1.3 F_{{nt}} - \\frac{{F_{{nt}}}}{{\\phi F_{{nv}}}} f_{{rv}} = 1.3({bolt_profile['F_nt']:.0f}) - \\frac{{{bolt_profile['F_nt']:.0f}}}{{0.75({bolt_profile['F_nv']:.0f})}}({f_rv:.1f}) = {F_nt_prime:.1f} \\text{{ MPa}} \\le F_{{nt}} $$")
        st.markdown(f"**Reduced tension capacity:** $\\phi R'_{{nt}} = 0.75 F'_{{nt}} A_b = $ **{bolt_t_cap_int:.2f} kN**")
        st.markdown(f"Critical tension demand $T_{{u,max}} =$ **{max_t_actual:.2f} kN** → "
                    f"($T_{{u,max}} / \\phi R'_{{nt}} =$ **{(max_t_actual/bolt_t_cap_int if bolt_t_cap_int > 0 else float('inf')):.2f}**)")

    conc_results = check_concrete_capacities(fc_mpa, h_ef, c_edge, d_b)
    phi_N_cb = conc_results.phi_N_cb
    phi_N_pn = conc_results.phi_N_pn

    with st.container(border=True):
        st.markdown("##### 📌 Step 4: Concrete Anchor Failure Modes (ACI 318)")
        st.caption("ตรวจสอบพฤติกรรมการหลุดและรูดของฝังในคอนกรีตเพื่อความปลอดภัย")

        st.markdown(f"- **Concrete Breakout Capacity (φN_cb):** **{phi_N_cb:.2f} kN**")
        st.markdown(f"- **Concrete Pullout Capacity (φN_pn):** **{phi_N_pn:.2f} kN**")
        st.markdown(f"- **Steel Tension Capacity (φR'nt):** **{bolt_t_cap_int:.2f} kN**")

        capacities = {
            "Steel Bolt Rupture (เหล็กโบลต์ขาด)": bolt_t_cap_int,
            "Concrete Breakout (คอนกรีตแตกกระเทาะ)": phi_N_cb,
            "Anchor Pullout (โบลต์รูดหลุด)": phi_N_pn,
        }
        governing_mode = min(capacities, key=capacities.get)
        min_cap = capacities[governing_mode]

        st.info(f"💡 **Governing Failure Mode:** จุดที่จะวิบัติก่อนคือ **{governing_mode}** ที่แรงดึง **{min_cap:.2f} kN**")

    t_pass = max_t_actual <= bolt_t_cap_int
    concrete_pass = max_t_actual <= min(phi_N_cb, phi_N_pn)
    v_pass = max_v_actual <= bolt_v_cap

    if t_pass and v_pass and concrete_pass:
        st.markdown("<div class='rec-card'>✅ <b>PASS:</b> โบลต์และฐานรากคอนกรีตสามารถรับแรงดึง-แรงเฉือนได้อย่างปลอดภัย</div>", unsafe_allow_html=True)
    else:
        errors = []
        if not t_pass:
            errors.append(f"แรงดึงชิ้นงาน ({max_t_actual:.2f} kN) > กำลังเหล็กโบลต์ φR'nt ({bolt_t_cap_int:.2f} kN)")
        if not concrete_pass:
            errors.append(f"แรงดึงชิ้นงาน ({max_t_actual:.2f} kN) > กำลังของคอนกรีต ({min(phi_N_cb, phi_N_pn):.2f} kN) — เสี่ยงเกิด Concrete Breakout/Pullout")
        if not v_pass:
            errors.append(f"แรงเฉือนชิ้นงาน ({max_v_actual:.2f} kN) > กำลังรับแรงเฉือนเหล็ก φRnv ({bolt_v_cap:.2f} kN)")
        error_text = "<br>".join([f"- {e}" for e in errors])
        st.markdown(f"<div class='danger-card'>❌ <b>FAIL: จุดเชื่อมต่อไม่ปลอดภัย</b><br>{error_text}</div>", unsafe_allow_html=True)
