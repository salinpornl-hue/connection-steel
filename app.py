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

# CSS Styling to clean up layout presentation
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #0f172a; text-align: center; margin-bottom: 2px; }
    .sub-title { font-size: 1rem; color: #475569; text-align: center; margin-bottom: 25px; }
    .section-banner { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 8px 15px; border-radius: 6px; font-weight: 600; margin-top: 15px; margin-bottom: 10px; }
    .metric-card { background-color: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center; }
    .metric-val { font-size: 1.4rem; font-weight: bold; color: #1e3a8a; }
    .status-pass { background-color: #dcfce7; color: #14532d; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .status-fail { background-color: #fee2e2; color: #7f1d1d; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🛡️ AISC Steel-Connection Ultimate Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>ระบบคำนวณพิกัดกลุ่มสลักเกลียวอิสระ ตรวจสอบระยะขอบ พิกัดชนเหล็ก และการแจกแจงแรงรอยเชื่อมตามมาตรฐาน AISC LRFD</div>", unsafe_allow_html=True)

# ==========================================
# 2. CONTROLS & SIDEBAR-STYLE COLUMNS
# ==========================================
col_ctrl, col_view = st.columns([1.0, 1.0])

with col_ctrl:
    st.markdown("<div class='section-banner'>1. มิติโครงสร้างและแรงประลัย (Structural Input)</div>", unsafe_allow_html=True)
    selected_profile = st.selectbox("เลือกหน้าตัดเสาเหล็ก (H-Beam มอก.):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
    prof = THAI_H_BEAM_PROFILES[selected_profile]
    
    c1, c2, c3, c4 = st.columns(4)
    d = c1.number_input("ลึกเสา d (mm)", value=prof["d"])
    bf = c2.number_input("กว้างปีก bf (mm)", value=prof["bf"])
    tw = c3.number_input("หนาเอว tw (mm)", value=prof["tw"])
    tf = c4.number_input("หนาปีก tf (mm)", value=prof["tf"])

    cx1, cx2, cx3, cx4 = st.columns(4)
    p_u_kn = cx1.number_input("แรงกด Pu (kN)", value=500.0)
    v_u_kn = cx2.number_input("แรงเฉือน Vu (kN)", value=100.0)
    m_u_knm = cx3.number_input("โมเมนต์ Mu (kN-m)", value=140.0)
    fc_mpa = cx4.number_input("ตอม่อ fc' (MPa)", value=28.0)

    st.markdown("<div class='section-banner'>2. มิติแผ่นเพลตฐานและขนาดสลักเกลียว (Base Plate & Bolt Spec)</div>", unsafe_allow_html=True)
    # Smart Recommendations Presets
    rec_B = math.ceil((bf + 150) / 10) * 10
    rec_N = math.ceil((d + 160) / 10) * 10
    
    cp1, cp2, cp3, cp4 = st.columns(4)
    B = cp1.number_input("กว้างเพลต B (mm)", value=float(rec_B))
    N = cp2.number_input("ยาวเพลต N (mm)", value=float(rec_N))
    tp = cp3.selectbox("หนาเพลต tp (mm)", THAI_PLATE_THICKNESSES, index=3)
    bolt_name = cp4.selectbox("ขนาดสลักเกลียว", list(THAI_ANCHOR_BOLTS.keys()), index=2)
    
    bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]
    d_b = bolt_profile["dia"]

    st.markdown("<div class='section-banner'>3. พิกัดตำแหน่งโบลต์รายตัว (Dynamic Bolt Coordinate Matrix)</div>", unsafe_allow_html=True)
    st.caption("แก้ไขพิกัด X, Y ได้ตามต้องการ โดยมีพิกัดเริ่มต้นแบบปลอดภัย (Safe Presets) หลบแนวเสาให้อัตโนมัติ")
    
    # Auto-seeding coordinates based on selected profile to prevent immediate crash
    init_x = (bf / 2.0) + 45.0
    init_y = (d / 2.0) + 50.0
    
    if "active_profile" not in st.session_state or st.session_state["active_profile"] != selected_profile:
        st.session_state["active_profile"] = selected_profile
        st.session_state["grid_data"] = pd.DataFrame({
            "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "X (mm)": [-init_x, init_x, -init_x, init_x, -init_x, init_x],
            "Y (mm)": [init_y, init_y, 0.0, 0.0, -init_y, -init_y]
        })

    edited_df = st.data_editor(st.session_state["grid_data"], num_rows="dynamic", use_container_width=True)
    num_bolts = len(edited_df)
    
    st.markdown("<div class='section-banner'>4. ขนาดรอยเชื่อมขา Fillet (Weld Size)</div>", unsafe_allow_html=True)
    weld_size_mm = st.slider("ขนาดรอยเชื่อมขา Fillet จริงหน้างาน (mm):", 3, 16, 8)

# ==========================================
# 3. ADVANCED COMPUTATIONAL ENGINE
# ==========================================
P_u_n = p_u_kn * 1000.0
V_u_n = v_u_kn * 1000.0
M_u_nmm = m_u_knm * 1000000.0

# 3.1 AISC Geometry Geometric Checks (Edge Distance & Spacing)
geometric_errors = []
min_s_req = 2.67 * d_b
min_edge_req = bolt_profile["min_edge"]

if num_bolts > 0:
    # A. ตรวจสอบระยะขอบเพลตรายตัว (Individual Edge Distance Checks)
    for idx, row in edited_df.iterrows():
        bx, by, bid = row["X (mm)"], row["Y (mm)"], row["Bolt ID"]
        edge_x1 = (B / 2.0) - bx
        edge_x2 = bx - (-B / 2.0)
        edge_y1 = (N / 2.0) - by
        edge_y2 = by - (-N / 2.0)
        
        actual_min_edge = min(edge_x1, edge_x2, edge_y1, edge_y2)
        if actual_min_edge < min_edge_req:
            geometric_errors.append(f"❌ <b>{bid}:</b> ระยะห่างถึงขอบเพลตเหลือน้อยเกินไป ({actual_min_edge:.1f} mm) ต่ำกว่าเกณฑ์ AISC ที่ต้องการ {min_edge_req} mm!")
        
        # ตรวจสอบการชนเนื้อเสาเหล็กคู่ต่อ
        if (abs(by) <= (d/2.0) + 35.0) and (abs(bx) <= (bf/2.0) + 35.0):
            geometric_errors.append(f"❌ <b>{bid}:</b> อยู่ในโซนชนปีก/เอวเสา หรือติดแนวเชื่อมเหล็กประเจขันไม่ได้!")

    # B. ตรวจสอบระยะห่างระหว่างสลักเกลียวคู่ต่อคู่ (Inter-bolt Spacing Checks)
    for i in range(num_bolts):
        for j in range(i + 1, num_bolts):
            b1 = edited_df.iloc[i]
            b2 = edited_df.iloc[j]
            dist = math.sqrt((b1["X (mm)"] - b2["X (mm)"])**2 + (b1["Y (mm)"] - b2["Y (mm)"])**2)
            if dist < min_s_req:
                geometric_errors.append(f"⚠️ <b>{b1['Bolt ID']} ถึง {b2['Bolt ID']}:</b> ระยะห่างกันสั้นเกินไป ({dist:.1f} mm) เสี่ยงต่อคอนกรีตระเบิดฉีกขาด! (AISC Min Spacing = {min_s_req:.1f} mm)")

# 3.2 Elastic Structural Mechanics
I_y_group = sum(edited_df["Y (mm)"]**2) if num_bolts > 0 else 1.0
tensions = []
for y in edited_df["Y (mm)"]:
    t_f = ((M_u_nmm * y) / I_y_group) + (-P_u_n / num_bolts) if num_bolts > 0 else 0
    tensions.append(max(0.0, t_f / 1000.0))
edited_df["Tension (kN)"] = tensions

# 3.3 Weld Mechanics Separation
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

if tp <= 13: min_weld_req = 5
elif tp <= 19: min_weld_req = 6
else: min_weld_req = 8
strength_weld_req = max_weld_demand / (0.75 * 0.60 * 490.0 * 0.707 / 1000.0)
final_weld_size = max(min_weld_req, math.ceil(strength_weld_req))

# 3.4 Concrete Bearing & Plate Stiffness
phi_c = 0.65
f_p_max = phi_c * 0.85 * fc_mpa
ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
Y_length = N if ecc <= (N/6.0) else max(0.0, (N/2.0) - (P_u_n / (2.0 * B * f_p_max)))
bearing_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
m_arm = (N - 0.95 * d) / 2.0
n_arm = (B - 0.80 * bf) / 2.0
t_req = max(m_arm, n_arm) * math.sqrt((2.0 * bearing_actual) / (0.90 * 245.0))

# ==========================================
# 4. ENGINEERING VISUALIZATION & OUTPUT
# ==========================================
with col_view:
    st.markdown("<div class='section-banner'>📋 ผลการตรวจสอบสลักเกลียวและรอยเชื่อม (Analysis Summary)</div>", unsafe_allow_html=True)
    
    # แจ้งเตือนข้อผิดพลาดทางเรขาคณิต (Geometrical Failures Billboard)
    if geometric_errors:
        st.markdown("<div class='danger-box'><b>⚠️ พบข้อขัดแย้งในระยะจัดวางสลักเกลียวตามเกณฑ์ AISC:</b><br>" + "<br>".join(geometric_errors) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='rec-box'>✅ <b>ระยะจัดวางสลักเกลียวสมบูรณ์แบบ:</b> ตรวจสอบระยะห่างระหว่างตัวและระยะวิ่งหาขอบแผ่นเพลตผ่านเกณฑ์ทั้งหมด ไม่มีการชนหน้าตัดเหล็กเสา</div>", unsafe_allow_html=True)
        
    # พิมพ์สรุปความต้องการของรอยเชื่อมแบบแยกส่วนต้านทาน
    weld_report = [
        {"ส่วนประกอบโครงสร้าง": "รอยเชื่อมปีกเสา (Flange Weld)", "กลไกการรับแรงหลัก": "Axial Force + Bending Moment Couple", "หน่วยแรงที่เกิดขึ้นจริง": f"{total_demand_flange:.3f} kN/mm"},
        {"ส่วนประกอบโครงสร้าง": "รอยเชื่อมเอวเสา (Web Weld)", "กลไกการรับแรงหลัก": "Major Shear Force Vector", "หน่วยแรงที่เกิดขึ้นจริง": f"{total_demand_web:.3f} kN/mm"}
    ]
    st.table(pd.DataFrame(weld_report))
    st.markdown(f"💡 **ข้อกำหนดการระบุแบบขยาย:** ขนาดรอยเชื่อมตามเกณฑ์คำนวณขั้นต่ำแรงประลัยที่ต้องการคือ **{strength_weld_req:.1f} mm** สรุปควรระบุในแบบที่: **{final_weld_size} mm**")

    # สรุปตารางความปลอดภัยภาพรวมทั้งหมด
    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area"]) / 1000.0
    
    final_matrix = [
        {"การประเมินกำลัง": "1. หน่วยแรงกดปะทะตอม่อคอนกรีต", "ค่าที่เกิดขึ้น": f"{bearing_actual:.1f} MPa", "ขีดจำกัดวิเคราะห์": f"{f_p_max:.1f} MPa", "ผลประเมิน": "✅ PASS" if bearing_actual<=f_p_max else "❌ FAIL"},
        {"การประเมินกำลัง": "2. ความหนาแผ่นเหล็กฐานฐาน (tp)", "ค่าที่เกิดขึ้น": f"{t_req:.1f} mm", "ขีดจำกัดวิเคราะห์": f"{tp:.1f} mm", "ผลประเมิน": "✅ PASS" if t_req<=tp else "❌ FAIL"},
        {"การประเมินกำลัง": "3. แรงดึงสลักเกลียวตัวที่วิกฤตที่สุด", "ค่าที่เกิดขึ้น": f"{max_t_actual:.1f} kN", "ขีดจำกัดวิเคราะห์": f"{bolt_t_cap:.1f} kN", "ผลประเมิน": "✅ PASS" if max_t_actual<=bolt_t_cap else "❌ FAIL"},
        {"การประเมินกำลัง": "4. ขีดหน่วยแรงลัพธ์รอยเชื่อมรอบหน้าตัด", "ค่าที่เกิดขึ้น": f"{max_weld_demand:.2f} kN/mm", "ขีดจำกัดวิเคราะห์": f"{weld_cap_per_mm:.2f} kN/mm", "ผลประเมิน": "✅ PASS" if max_weld_demand<=weld_cap_per_mm else "❌ FAIL"}
    ]
    st.dataframe(pd.DataFrame(final_matrix), use_container_width=True)

    # ==========================================
    # 5. HIGH-VISIBILITY 3D PLOTLY RENDER
    # ==========================================
    fig = go.Figure()
    
    # Base Plate Mesh
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#475569', opacity=0.85, name='Plate'))
    # H-Beam Profile Mesh
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', name='Column'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#334155', showlegend=False))

    # Colored Welds Core Lines
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), name='Flange Welds'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[tw/2, tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), name='Web Welds'))
    fig.add_trace(go.Scatter3d(x=[-tw/2, -tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), showlegend=False))

    # Dynamic Bolt Vector Rendering
    for _, row in edited_df.iterrows():
        bx, by, tf_bolt, b_id = row["X (mm)"], row["Y (mm)"], row["Tension (kN)"], row["Bolt ID"]
        bolt_col = '#ef4444' if tf_bolt > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-180, tp+20], mode='lines+markers', marker=dict(size=6, color=bolt_col), line=dict(color=bolt_col, width=6), showlegend=False))
        
        if tf_bolt > 0:
            z_top = tp + 20 + 40 + (tf_bolt * 1.2)
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[tp+20, z_top], mode='lines', line=dict(color='#b91c1c', width=9), showlegend=False))
            fig.add_trace(go.Cone(x=[bx], y=[by], z=[z_top], u=[0], v=[0], w=[35], sizemode="absolute", sizeref=20, showscale=False, colorscale=[[0,'#b91c1c'],[1,'#b91c1c']], showlegend=False))

    # Global Loads Arrow Vectors (100% Render Proof Line-Cone Engine)
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[tp+550, tp+400], mode='lines', line=dict(color='black', width=12), name='Pu Force'))
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+400], u=[0], v=[0], w=[-50], sizemode="absolute", sizeref=30, showscale=False, colorscale=[[0,'black'],[1,'black']], showlegend=False))

    if v_u_kn > 0:
        fig.add_trace(go.Scatter3d(x=[0,0], y=[-150,0], z=[tp+400, tp+400], mode='lines', line=dict(color='#9333ea', width=12), name='Vu Force'))
        fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+400], u=[0], v=[50], w=[0], sizemode="absolute", sizeref=30, showscale=False, colorscale=[[0,'#9333ea'],[1,'#9333ea']], showlegend=False))

    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.1))), margin=dict(l=0, r=0, b=0, t=0), height=600)
    st.plotly_chart(fig, use_container_width=True)
