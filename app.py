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
st.markdown("<div class='sub-title'>ระบบคำนวณพิกัดกลุ่มสลักเกลียวอิสระ ตรวจสอบระยะขอบ พิกัดชนเหล็ก และการแจกแจงแรงรอยเชื่อมตามมาตรฐาน AISC LRFD</div>", unsafe_allow_html=True)

# ==========================================
# 2. DEFINING THE 3-COLUMN STUDIO LAYOUT
# ==========================================
col_input, col_matrix, col_result = st.columns([0.9, 1.0, 1.1])

# ------------------------------------------
# COLUMN 1: STRUCTURAL INPUT PARAMETERS
# ------------------------------------------
with col_input:
    st.markdown("<div class='column-title'>🎛️ 1. ข้อมูลส่วนคู่ต่อ & แรงประลัย</div>", unsafe_allow_html=True)
    
    selected_profile = st.selectbox("หน้าตัดเสาเหล็กคู่ต่อ (H-Beam มอก.):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
    prof = THAI_H_BEAM_PROFILES[selected_profile]
    
    with st.container(border=True):
        st.caption("📐 มิติหน้าตัดเสาเหล็ก (mm)")
        c1, c2 = st.columns(2)
        d = c1.number_input("ลึกเสา d", value=prof["d"])
        bf = c2.number_input("กว้างปีก bf", value=prof["bf"])
        tw = c1.number_input("หนาเอว tw", value=prof["tw"])
        tf = c2.number_input("หนาปีก tf", value=prof["tf"])

    with st.container(border=True):
        st.caption("⚡ แรงประลัยที่กระทำต่อจุดต่อ (LRFD Load)")
        cx1, cx2 = st.columns(2)
        p_u_kn = cx1.number_input("แรงกด Pu (kN)", value=500.0)
        v_u_kn = cx2.number_input("แรงเฉือน Vu (kN)", value=100.0)
        m_u_knm = cx1.number_input("โมเมนต์ Mu (kN-m)", value=140.0)
        fc_mpa = cx2.number_input("ตอม่อ fc' (MPa)", value=28.0)

    with st.container(border=True):
        st.caption("🔩 แผ่นฐานและขนาดสลักเกลียว")
        rec_B = math.ceil((bf + 150) / 10) * 10
        rec_N = math.ceil((d + 160) / 10) * 10
        
        if "plate_B" not in st.session_state: st.session_state["plate_B"] = float(rec_B)
        if "plate_N" not in st.session_state: st.session_state["plate_N"] = float(rec_N)
        
        B = st.number_input("กว้างเพลต B (mm)", value=st.session_state["plate_B"], key="plate_B")
        N = st.number_input("ยาวเพลต N (mm)", value=st.session_state["plate_N"], key="plate_N")
        tp = st.selectbox("หนาเพลต tp (mm)", THAI_PLATE_THICKNESSES, index=3)
        bolt_name = st.selectbox("เลือกขนาดสลักเกลียว", list(THAI_ANCHOR_BOLTS.keys()), index=2)
        
        bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]
        d_b = bolt_profile["dia"]
        
    weld_size_mm = st.slider("ขนาดรอยเชื่อมขา Fillet ใช้งานจริง (mm):", 3, 16, 8)

# ------------------------------------------
# COLUMN 2: INTERACTIVE COORDINATE MATRIX & ALERTS
# ------------------------------------------
with col_matrix:
    st.markdown("<div class='column-title'>🎯 2. พิกัดและระยะจัดวางสลักเกลียว</div>", unsafe_allow_html=True)
    st.caption("พิมพ์แก้ไขพิกัด X, Y บนแผ่นเพลตได้อิสระ โดยจุด (0,0) อยู่ที่จุดศูนย์กลางของเสาเหล็ก")
    
    init_x = (bf / 2.0) + 45.0
    init_y = (d / 2.0) + 50.0
    
    if "active_profile" not in st.session_state or st.session_state["active_profile"] != selected_profile:
        st.session_state["active_profile"] = selected_profile
        st.session_state["grid_data"] = pd.DataFrame({
            "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "X (mm)": [-init_x, init_x, -init_x, init_x, -init_x, init_x],
            "Y (mm)": [init_y, init_y, 0.0, 0.0, -init_y, -init_y]
        })

    # [NEW] Auto-Resize Engine Button
    if st.button("🤖 Auto-Resize (แก้พิกัดโบลต์ + ขยายเพลตอัตโนมัติ)", use_container_width=True):
        fixed_matrix = st.session_state["grid_data"].copy()
        max_abs_x = 0.0
        max_abs_y = 0.0
        
        # Step 1: ขยับโบลต์หนีเสา
        for idx, row in fixed_matrix.iterrows():
            curr_x, curr_y = row["X (mm)"], row["Y (mm)"]
            sign_x = 1.0 if curr_x >= 0 else -1.0
            sign_y = 1.0 if curr_y >= 0 else -1.0
            
            if abs(curr_x) < init_x: curr_x = init_x * sign_x
            if abs(curr_y) < (d/2.0) + 35.0 and abs(curr_y) > 0.0: curr_y = init_y * sign_y
            
            fixed_matrix.at[idx, "X (mm)"] = curr_x
            fixed_matrix.at[idx, "Y (mm)"] = curr_y
            
            # เก็บค่าตำแหน่งที่กว้างที่สุดไว้ประเมินแผ่นเพลต
            max_abs_x = max(max_abs_x, abs(curr_x))
            max_abs_y = max(max_abs_y, abs(curr_y))
            
        st.session_state["grid_data"] = fixed_matrix
        
        # Step 2: ขยายแผ่นเพลตให้ครอบคลุมระยะขอบ (Edge Distance)
        req_B = (max_abs_x + bolt_profile["min_edge"]) * 2.0
        req_N = (max_abs_y + bolt_profile["min_edge"]) * 2.0
        
        # ปัดเศษขึ้นให้เป็นเลขกลมๆ (หลักสิบ)
        st.session_state["plate_B"] = float(math.ceil(req_B / 10.0) * 10.0)
        st.session_state["plate_N"] = float(math.ceil(req_N / 10.0) * 10.0)
        
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
                geometric_errors.append(f"❌ <b>{bid}:</b> ระยะขอบเพลตสั้นไป ({actual_min_edge:.1f} mm < {min_edge_req} mm)")
            if (abs(by) <= (d/2.0) + 35.0) and (abs(bx) <= (bf/2.0) + 35.0):
                geometric_errors.append(f"❌ <b>{bid}:</b> ตกอยู่ในระยะขัดแย้ง ชนเสาหรือชิดเกินประแจขัน")

        for i in range(num_bolts):
            for j in range(i + 1, num_bolts):
                b1, b2 = edited_df.iloc[i], edited_df.iloc[j]
                dist = math.sqrt((b1["X (mm)"] - b2["X (mm)"])**2 + (b1["Y (mm)"] - b2["Y (mm)"])**2)
                if dist < min_s_req:
                    geometric_errors.append(f"⚠️ <b>{b1['Bolt ID']}-{b2['Bolt ID']}:</b> ระยะห่างชิดเกินไป ({dist:.1f} mm < {min_s_req:.1f} mm)")

    st.markdown("#### 🚨 ระบบตรวจสอบระยะทางเรขาคณิต")
    if geometric_errors:
        st.markdown("<div class='danger-card'>" + "<br>".join(geometric_errors) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='rec-card'>✅ <b>ผ่านเกณฑ์ทางเรขาคณิตทั้งหมด</b> ไม่มีอาการชนเนื้อเสาเหล็ก</div>", unsafe_allow_html=True)

# ------------------------------------------
# COLUMN 3: ENGINEERING DASHBOARD & 3D MODEL
# ------------------------------------------
with col_result:
    st.markdown("<div class='column-title'>📊 3. บทสรุปทางวิศวกรรม & โมเดล 3D</div>", unsafe_allow_html=True)
    
    # --- ENGINEERING MECHANICS CALCULATION ---
    P_u_n, V_u_n, M_u_nmm = p_u_kn * 1000.0, v_u_kn * 1000.0, m_u_knm * 1000000.0

    I_y_group = sum(edited_df["Y (mm)"]**2) if num_bolts > 0 else 1.0
    tensions = []
    for y in edited_df["Y (mm)"]:
        t_f = ((M_u_nmm * y) / I_y_group) + (-P_u_n / num_bolts) if num_bolts > 0 else 0
        tensions.append(max(0.0, t_f / 1000.0))
    edited_df["Tension (kN)"] = tensions

    # [NEW] Weld Lengths Included
    l_flange = 4.0 * bf
    l_web = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0
    l_total = l_flange + l_web

    weld_stress_axial = (P_u_n / l_total) / 1000.0 if l_total > 0 else 0
    weld_stress_moment = (M_u_nmm / (2.0 * bf * (d - tf))) / 1000.0 if bf > 0 else 0
    weld_stress_shear = (V_u_n / l_web) / 1000.0 if l_web > 0 else 0

    total_demand_flange = weld_stress_axial + weld_stress_moment
    total_demand_web = math.sqrt(weld_stress_axial**2 + weld_stress_shear**2)
    max_weld_demand = max(total_demand_flange, total_demand_web)
    weld_cap_per_mm = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0

    min_weld_req = 5 if tp <= 13 else (6 if tp <= 19 else 8)
    strength_weld_req = max_weld_demand / (0.75 * 0.60 * 490.0 * 0.707 / 1000.0)
    final_weld_size = max(min_weld_req, math.ceil(strength_weld_req))

    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    bearing_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
    m_arm = (N - 0.95 * d) / 2.0
    n_arm = (B - 0.80 * bf) / 2.0
    t_req = max(m_arm, n_arm) * math.sqrt((2.0 * bearing_actual) / (0.90 * 245.0))

    # --- RENDER SUMMARY DASHBOARD ---
    st.markdown(f"""
    <div class='rec-card'>
    <b>📋 สรุปขนาดและปริมาณรอยเชื่อมที่หน้างาน:</b><br>
    - รอยเชื่อมปีกเสา: <b>รับแรง {total_demand_flange:.2f} kN/mm</b> (ความยาวเชื่อม {l_flange:.0f} mm)<br>
    - รอยเชื่อมเอวเสา: <b>รับแรง {total_demand_web:.2f} kN/mm</b> (ความยาวเชื่อม {l_web:.0f} mm)<br>
    🎯 <b>ขนาดแนะนำให้ระบุในแบบโครงสร้างจริง: {final_weld_size} mm</b>
    </div>
    """, unsafe_allow_html=True)

    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area"]) / 1000.0
    
    final_matrix = [
        {"การประเมินโครงสร้าง": "1. แรงกดผิวคอนกรีต", "ใช้จริง": f"{bearing_actual:.1f} MPa", "รับได้": f"{f_p_max:.1f} MPa", "สถานะ": "PASS" if bearing_actual<=f_p_max else "FAIL"},
        {"การประเมินโครงสร้าง": "2. ความหนาแผ่นเพลต", "ใช้จริง": f"{t_req:.1f} mm", "รับได้": f"{tp:.1f} mm", "สถานะ": "PASS" if t_req<=tp else "FAIL"},
        {"การประเมินโครงสร้าง": "3. แรงดึงโบลต์วิกฤต", "ใช้จริง": f"{max_t_actual:.1f} kN", "รับได้": f"{bolt_t_cap:.1f} kN", "สถานะ": "PASS" if max_t_actual<=bolt_t_cap else "FAIL"},
        {"การประเมินโครงสร้าง": "4. แรงลัพธ์แนวเชื่อม", "ใช้จริง": f"{max_weld_demand:.2f} kN/mm", "รับได้": f"{weld_cap_per_mm:.2f} kN/mm", "สถานะ": "PASS" if max_weld_demand<=weld_cap_per_mm else "FAIL"}
    ]
    st.dataframe(pd.DataFrame(final_matrix), use_container_width=True, hide_index=True)

    # --- 3D INTERACTIVE GRAPHICS ENGINE (Improved Proportions) ---
    fig = go.Figure()
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

    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[tp+480, tp+350], mode='lines', line=dict(color='black', width=10), name='Pu Force'))
    
    # [NEW] Adjusted height to fit column better
    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.1))), margin=dict(l=0, r=0, b=0, t=0), height=550)
    st.plotly_chart(fig, use_container_width=True)
