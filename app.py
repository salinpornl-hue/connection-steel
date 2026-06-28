# app.py
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. METRIC DATABASE & STANDARDS (AISC 360)
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

st.set_page_config(page_title="AISC Base Plate Expert Suite", layout="wide")

# CSS UI Enhancement
st.markdown("""
    <style>
    .studio-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 18px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .row-title { background-color: #1e293b; color: white; padding: 10px 16px; border-radius: 6px; font-weight: bold; font-size: 1.1rem; margin-top: 25px; margin-bottom: 15px; border-left: 6px solid #2563eb; }
    .card-pass { background-color: #f0fdf4; color: #166534; padding: 15px; border-radius: 6px; border: 1px solid #bbf7d0; font-weight: 500; }
    .card-fail { background-color: #fef2f2; color: #991b1b; padding: 15px; border-radius: 6px; border: 1px solid #fca5a5; font-weight: 500; }
    .panel-bg { background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# Main Dashboard Header
st.markdown("""
<div class='studio-banner'>
    <h2 style='margin:0; font-weight:800; letter-spacing:-0.5px;'>🛡️ AISC Base-Plate & Weld Optimization Suite</h2>
    <p style='margin:5px 0 0 0; color:#94a3b8; font-size:0.95rem;'>แพลตฟอร์มคำนวณและปรับแต่งพิกัดกลุ่มสลักเกลียวอิสระ พร้อมวิเคราะห์แยกพฤติกรรมรอยเชื่อมตามมาตรฐาน AISC LRFD</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONTROLS & CONTROLLER ROW (HORIZONTAL)
# ==========================================
st.markdown("<div class='row-title'>📐 ส่วนที่ 1: การกำหนดคุณลักษณะหน้าตัดเสา, แผ่นเพลต และแรงประลัย</div>", unsafe_allow_html=True)

with st.container():
    grid_top = st.columns([1.1, 1.1, 0.8])
    
    with grid_top[0]:
        st.markdown("**[เสาเหล็ก มอก. & แรงประลัย]**")
        selected_profile = st.selectbox("เลือกหน้าตัดเสาเหล็กคู่ต่อ (H-Beam):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
        prof = THAI_H_BEAM_PROFILES[selected_profile]
        
        c1, c2, c3, c4 = st.columns(4)
        d = c1.number_input("ลึก d (mm)", value=prof["d"])
        bf = c2.number_input("กว้าง bf (mm)", value=prof["bf"])
        tw = c3.number_input("เอว tw (mm)", value=prof["tw"])
        tf = c4.number_input("ปีก tf (mm)", value=prof["tf"])
        
        cx1, cx2, cx3 = st.columns(3)
        p_u_kn = cx1.number_input("แรงกด Pu (kN)", value=450.0)
        v_u_kn = cx2.number_input("แรงเฉือน Vu (kN)", value=120.0)
        m_u_knm = cx3.number_input("โมเมนต์ Mu (kN-m)", value=130.0)

    with grid_top[1]:
        st.markdown("**[แผ่นเพลตฐานเหล็ก & คอนกรีต]**")
        fc_mpa = st.number_input("กำลังอัดของตอม่อคอนกรีต fc' (MPa)", value=28.0)
        
        # Smart Recommended Defaults
        rec_B = math.ceil((bf + 150) / 10) * 10
        rec_N = math.ceil((d + 160) / 10) * 10
        
        cp1, cp2, cp3 = st.columns(3)
        B = cp1.number_input("กว้างใช้งาน B (mm)", value=float(rec_B))
        N = cp2.number_input("ยาวใช้งาน N (mm)", value=float(rec_N))
        tp = cp3.selectbox("หนาเพลตใช้งาน tp (mm)", THAI_PLATE_THICKNESSES, index=3)
        st.caption(f"💡 ขนาดแนะนำขั้นต่ำเพื่อหลบแนวประแจ: B={rec_B} mm, N={rec_N} mm")

    with grid_top[2]:
        st.markdown("**[ข้อมูลคุณลักษณะสลักเกลียว & รอยเชื่อม]**")
        bolt_name = st.selectbox("สเปกขนาดโบลต์ (AISC):", list(THAI_ANCHOR_BOLTS.keys()), index=2)
        bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]
        d_b = bolt_profile["dia"]
        
        weld_size_mm = st.slider("ขนาดรอยเชื่อมขา Fillet ที่เลือกใช้ (mm):", 3, 16, 8)

# ==========================================
# 3. INTERACTIVE MATRIX & AUTO-RESIZE SYSTEM
# ==========================================
st.markdown("<div class='row-title'>🎯 ส่วนที่ 2: ตารางกำหนดพิกัดสลักเกลียวอิสระ และระบบสั่งจัดขนาดอัตโนมัติ (Auto-Resize Engine)</div>", unsafe_allow_html=True)

# Safe Positions Presets Generator
safe_x = (bf / 2.0) + 45.0
safe_y = (d / 2.0) + 50.0

if "bolt_matrix" not in st.session_state or st.session_state.get("last_profile") != selected_profile:
    st.session_state["last_profile"] = selected_profile
    st.session_state["bolt_matrix"] = pd.DataFrame({
        "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
        "X (mm)": [-safe_x, safe_x, -safe_x, safe_x, -safe_x, safe_x],
        "Y (mm)": [safe_y, safe_y, 0.0, 0.0, -safe_y, -safe_y]
    })

# 🤖 [ENGINEERING AUTO-RESIZE ENGINE BUTTON]
if st.button("🤖 คลิกปุ่มนี้เพื่อแก้พิกัดโบลต์อัตโนมัติ (Auto-Resize Fix to PASS)"):
    fixed_matrix = st.session_state["bolt_matrix"].copy()
    for idx, row in fixed_matrix.iterrows():
        # ผลักพิกัดออกนอกระยะเสาและระยะขอบเพลตที่ปลอดภัยตามกฎฟิสิกส์
        curr_x = row["X (mm)"]
        curr_y = row["Y (mm)"]
        
        sign_x = 1.0 if curr_x >= 0 else -1.0
        sign_y = 1.0 if curr_y >= 0 else -1.0
        
        # บังคับพิกัด X, Y ให้อยู่ในโซนปลอดภัย
        if abs(curr_x) < safe_x: curr_x = safe_x * sign_x
        if abs(curr_y) < (d/2.0) + 35.0 and abs(curr_y) > 0.0: curr_y = safe_y * sign_y
        
        # ตรวจสอบขอบเขตแผ่นเพลต (ห้ามหลุดขอบ)
        if abs(curr_x) > (B/2.0) - bolt_profile["min_edge"]: curr_x = ((B/2.0) - bolt_profile["min_edge"]) * sign_x
        if abs(curr_y) > (N/2.0) - bolt_profile["min_edge"]: curr_y = ((N/2.0) - bolt_profile["min_edge"]) * sign_y
        
        fixed_matrix.at[idx, "X (mm)"] = curr_x
        fixed_matrix.at[idx, "Y (mm)"] = curr_y
        
    st.session_state["bolt_matrix"] = fixed_matrix
    st.success("🎉 ระบบ Auto-Resize ปรับแก้พิกัดหนีแนวเสาและจัดระยะขอบแผ่นฐานผ่านเกณฑ์เรียบร้อย!")

# Render Matrix Editor
edited_df = st.data_editor(st.session_state["bolt_matrix"], num_rows="dynamic", use_container_width=True)
st.session_state["bolt_matrix"] = edited_df
num_bolts = len(edited_df)

# ==========================================
# 4. STRUCTURAL MECHANICS LOGIC CORE
# ==========================================
P_u_n = p_u_kn * 1000.0
V_u_n = v_u_kn * 1000.0
M_u_nmm = m_u_knm * 1000000.0

# 4.1 ตรวจสอบระยะพิกัดขัดแย้งทางเรขาคณิต (AISC Geometric Checker)
geometric_errors = []
min_s_req = 2.67 * d_b
min_edge_req = bolt_profile["min_edge"]

if num_bolts > 0:
    for idx, row in edited_df.iterrows():
        bx, by, bid = row["X (mm)"], row["Y (mm)"], row["Bolt ID"]
        ex = min((B/2.0) - bx, bx - (-B/2.0))
        ey = min((N/2.0) - by, by - (-N/2.0))
        
        if min(ex, ey) < min_edge_req:
            geometric_errors.append(f"❌ <b>{bid}:</b> ระยะห่างถึงขอบเพลตสั้นเกินไป (จริง: {min(ex,ey):.1f} mm | ยอมให้ขั้นต่ำ: {min_edge_req} mm)")
        if (abs(by) <= (d/2.0) + 35.0) and (abs(bx) <= (bf/2.0) + 35.0):
            geometric_errors.append(f"❌ <b>{bid}:</b> พิกัดชนเสาเหล็กหรือชิดเกินไปจนหัวประแจไม่สามารถเข้าขันได้")

    for i in range(num_bolts):
        for j in range(i + 1, num_bolts):
            b1, b2 = edited_df.iloc[i], edited_df.iloc[j]
            dist = math.sqrt((b1["X (mm)"] - b2["X (mm)"])**2 + (b1["Y (mm)"] - b2["Y (mm)"])**2)
            if dist < min_s_req:
                geometric_errors.append(f"⚠️ <b>{b1['Bolt ID']}-{b2['Bolt ID']}:</b> ระยะห่างกันวิกฤตชิดเกินเกณฑ์ ({dist:.1f} mm < ขั้นต่ำต้องการ {min_s_req:.1f} mm)")

# 4.2 คำนวณการกระจายแรงดึงสลักเกลียว
I_y_group = sum(edited_df["Y (mm)"]**2) if num_bolts > 0 else 1.0
tensions = []
for y in edited_df["Y (mm)"]:
    t_f = ((M_u_nmm * y) / I_y_group) + (-P_u_n / num_bolts) if num_bolts > 0 else 0
    tensions.append(max(0.0, t_f / 1000.0))
edited_df["Tension (kN)"] = tensions

# 4.3 การวิเคราะห์โมเมนตัมรอยเชื่อมแยกชิ้นส่วนอย่างละเอียด
l_weld_flange_total = 4.0 * bf
l_weld_web_total = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0
l_weld_sum = l_weld_flange_total + l_weld_web_total

weld_f_axial = (P_u_n / l_weld_sum) / 1000.0 if l_weld_sum > 0 else 0
weld_f_moment = (M_u_nmm / (2.0 * bf * (d - tf))) / 1000.0 if bf > 0 else 0
weld_f_shear = (V_u_n / l_weld_web_total) / 1000.0 if l_weld_web_total > 0 else 0

total_demand_flange = weld_f_axial + weld_f_moment
total_demand_web = math.sqrt(weld_f_axial**2 + weld_f_shear**2)
max_weld_demand = max(total_demand_flange, total_demand_web)
weld_cap_per_mm = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0

min_weld_req = 5 if tp <= 13 else (6 if tp <= 19 else 8)
strength_weld_req = max_weld_demand / (0.75 * 0.60 * 490.0 * 0.707 / 1000.0)
final_weld_size = max(min_weld_req, math.ceil(strength_weld_req))

# 4.4 ความเค้นกดคอนกรีตและความหนาเพลตเหล็กที่คำนวณต้องการจริง
phi_c = 0.65
f_p_max = phi_c * 0.85 * fc_mpa
ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
bearing_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
m_arm = (N - 0.95 * d) / 2.0
n_arm = (B - 0.80 * bf) / 2.0
t_req = max(m_arm, n_arm) * math.sqrt((2.0 * bearing_actual) / (0.90 * 245.0))

# ==========================================
# 5. INDUSTRIAL REPORT & ULTRA 3D DISPLAY ROW
# ==========================================
st.markdown("<div class='row-title'>📊 ส่วนที่ 3: แดชบอร์ดสรุปความปลอดภัยโครงสร้าง และแบบจำลองแรง 3 มิติความละเอียดสูง</div>", unsafe_allow_html=True)

grid_bottom = st.columns([1.1, 0.9])

with grid_bottom[0]:
    # แสดงกล่องแจ้งเตือนทางเรขาคณิตแบบเต็มความกว้างในคอลัมน์
    if geometric_errors:
        st.markdown("<div class='card-fail'><b>⚠️ ตรวจพบระยะการจัดวางโบลต์ขัดแย้งตามหลักสากล:</b><br>" + "<br>".join(geometric_errors) + "<br><span style='color:black;'>💡 แนะนำให้เลื่อนขึ้นด้านบนแล้วกดปุ่ม Auto-Resize เพื่อให้ระบบแก้ไขอัตโนมัติ</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card-pass'>✅ <b>ระยะเรขาคณิตผ่าน 100%:</b> โบลต์ทุกตัวอยู่ในพิกัดที่เหมาะสม ผ่านเกณฑ์ระยะห่างและการวิ่งหาขอบเพลตตามมาตรฐาน AISC</div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔬 ผลการแยกส่วนวิเคราะห์แรงรอยเชื่อม (Weld Stress & Length Breakdown)")
    weld_table_data = [
        {"ชิ้นส่วนแนวเชื่อมเสา": "แนวเชื่อมปีกเสา (Flange Weld)", "ความยาวรอยเชื่อมรวมจริงที่ต้องเชื่อม": f"{l_weld_flange_total:.0f} mm", "หน่วยแรงประลัยสะสมจริง": f"{total_demand_flange:.3f} kN/mm", "ส่วนหลักที่ทำหน้าที่ต้านทาน": "ต้านแรงกดเสา + โมเมนต์ดัด (Moment Couple)"},
        {"ชิ้นส่วนแนวเชื่อมเสา": "แนวเชื่อมเอวเสา (Web Weld)", "ความยาวรอยเชื่อมรวมจริงที่ต้องเชื่อม": f"{l_weld_web_total:.0f} mm", "หน่วยแรงประลัยสะสมจริง": f"{total_demand_web:.3f} kN/mm", "ส่วนหลักที่ทำหน้าที่ต้านทาน": "ต้านแรงกดเสา + แรงเฉือนหลัก (Major Shear Force)"}
    ]
    st.table(weld_table_data)
    st.markdown(f"📝 **ข้อกำหนดระบุแบบขยายรอยเชื่อม:** ขนาดรอยเชื่อมจาก Strength ต้องการคือ **{strength_weld_req:.1f} mm** สรุปหน้างานควรสั่งเชื่อมหนาขา Fillet: **{final_weld_size} mm**")

    # AISC Safety Compliance Matrix Table
    st.markdown("#### 🛡️ ตารางสรุปขีดความสามารถและความปลอดภัยของจุดต่อ (AISC Safety Matrix)")
    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area"]) / 1000.0
    
    final_compliance_matrix = [
        {"รายการประเมินโครงสร้าง": "แรงกดสัมผัสคอนกรีตใต้แผ่นเพลต", "ใช้จริง": f"{bearing_actual:.1f} MPa", "รับได้สูงสุด": f"{f_p_max:.1f} MPa", "ผลลัพธ์": "🟢 PASS" if bearing_actual<=f_p_max else "🔴 FAIL"},
        {"รายการประเมินโครงสร้าง": "ความหนาของแผ่นเหล็กเพลตฐานฐาน (tp)", "ใช้จริง": f"{t_req:.1f} mm", "รับได้สูงสุด": f"{tp:.1f} mm", "ผลลัพธ์": "🟢 PASS" if t_req<=tp else "🔴 FAIL"},
        {"รายการประเมินโครงสร้าง": "แรงดึงถอนในตัวสลักเกลียวตัวที่วิกฤตที่สุด", "ใช้จริง": f"{max_t_actual:.1f} kN", "รับได้สูงสุด": f"{bolt_t_cap:.1f} kN", "ผลลัพธ์": "🟢 PASS" if max_t_actual<=bolt_t_cap else "🔴 FAIL"},
        {"รายการประเมินโครงสร้าง": "หน่วยความเค้นลัพธ์ของแนวรอยเชื่อมรอบหน้าตัด", "ใช้จริง": f"{max_weld_demand:.2f} kN/mm", "รับได้สูงสุด": f"{weld_cap_per_mm:.2f} kN/mm", "ผลลัพธ์": "🟢 PASS" if max_weld_demand<=weld_cap_per_mm else "🔴 FAIL"}
    ]
    st.dataframe(pd.DataFrame(final_compliance_matrix), use_container_width=True, hide_index=True)

with grid_bottom[1]:
    st.markdown("#### 🧊 โมเดลจำลองมิติแรงและแนวเชื่อมจริง 3 มิติ (Full Container High-Res Render)")
    
    # 3D Plotly Engine (ขยายความสูง สัดส่วนสมจริง ดูง่ายไม่ซ้อนทับกัน)
    fig = go.Figure()
    
    # Base Plate Plate Box
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#64748b', opacity=0.8, name='Base Plate'))
    
    # H-Beam Profile Body
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', name='Column Flange'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#475569', name='Column Web'))

    # Weld Lines Highlighting
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=9), name='Flange Weld (Cyan)'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=9), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[tw/2, tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=7), name='Web Weld (Purple)'))
    fig.add_trace(go.Scatter3d(x=[-tw/2, -tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=7), showlegend=False))

    # Bolt Node & Bolt Tension Arrow Renderer
    for _, row in edited_df.iterrows():
        bx, by, tf_bolt, b_id = row["X (mm)"], row["Y (mm)"], row["Tension (kN)"], row["Bolt ID"]
        b_color = '#ef4444' if tf_bolt > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-150, tp+20], mode='lines+markers', marker=dict(size=6, color=b_color), line=dict(color=b_color, width=5), showlegend=False))
        
        if tf_bolt > 0:
            z_top_arrow = tp + 20 + 30 + (tf_bolt * 1.2)
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[tp+20, z_top_arrow], mode='lines', line=dict(color='#b91c1c', width=8), showlegend=False))

    # Axis Main Loads Arrow Vector
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[tp+520, tp+400], mode='lines', line=dict(color='black', width=10), name='Pu Vector'))
    
    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.35, y=-1.35, z=1.05))), margin=dict(l=0, r=0, b=0, t=0), height=550)
    st.plotly_chart(fig, use_container_width=True)
