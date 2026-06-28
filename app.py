# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. METRIC DATABASE & MATERIALS
# ================= ================= =================
THAI_PLATE_THICKNESSES_MM = {
    "12 mm": 12.0, "16 mm": 16.0, "19 mm": 19.0, "22 mm": 22.0, 
    "25 mm": 25.0, "28 mm": 28.0, "32 mm": 32.0, "38 mm": 38.0, "50 mm": 50.0
}

THAI_ANCHOR_BOLTS_MM = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area_as": 157.0, "F_nt": 300.0, "F_nv": 180.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area_as": 245.0, "F_nt": 300.0, "F_nv": 180.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area_as": 353.0, "F_nt": 300.0, "F_nv": 180.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area_as": 561.0, "F_nt": 600.0, "F_nv": 360.0}
}

st.set_page_config(page_title="AISC-Thai Expert Connection", layout="wide")
st.markdown("""
    <style>
    .step-header { background-color: #0d47a1; color: white; padding: 10px 15px; border-radius: 4px; margin-top: 15px; margin-bottom: 12px; font-weight: bold; }
    .error-box { background-color: #ffebee; color: #b71c1c; padding: 12px; border-radius: 4px; border-left: 6px solid #e53935; margin-bottom: 10px; font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 AISC Custom-Matrix & Force Vector Engine")
st.caption("ระบบกำหนดพิกัดโบลต์อิสระ พร้อมลูกศรเวกเตอร์ 3 มิติแบบ Custom Drawn | AISC 360 LRFD")

# ================= ================= =================
# 2. BULLETPROOF 3D VECTOR GENERATOR
# ================= ================= =================
def draw_force_vector(fig, start_pt, end_pt, color, name):
    """ฟังก์ชันวาดลูกศรแบบทนทาน (เส้นหนา + หัวลูกศร) ป้องกันบั๊กไม่แสดงผล"""
    # วาดก้านลูกศร
    fig.add_trace(go.Scatter3d(
        x=[start_pt[0], end_pt[0]], y=[start_pt[1], end_pt[1]], z=[start_pt[2], end_pt[2]],
        mode='lines', line=dict(color=color, width=12), name=name
    ))
    # วาดหัวลูกศร
    vec_x, vec_y, vec_z = end_pt[0]-start_pt[0], end_pt[1]-start_pt[1], end_pt[2]-start_pt[2]
    fig.add_trace(go.Cone(
        x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]],
        u=[vec_x], v=[vec_y], w=[vec_z],
        sizemode="absolute", sizeref=60, showscale=False, colorscale=[[0, color], [1, color]], showlegend=False
    ))

def generate_bulletproof_3d(B, N, tp, d, bf, tw, tf, bolt_coords, bolt_forces, Y_length, P_u, V_u, M_u):
    fig = go.Figure()
    h_col = 500.0 

    # ฐานคอนกรีต & แผ่นเพลต
    fig.add_trace(go.Mesh3d(x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8], y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8], z=[-400, -400, -400, -400, 0, 0, 0, 0], color='lightgrey', opacity=0.15, name='Concrete'))
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#607D8B', opacity=0.9, name='Base Plate'))

    # หน้าตัดเสา H-Beam
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#37474F', name='Flange 1'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#37474F', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#455A64', name='Web'))

    # กลุ่มโบลต์
    for idx, (bx, by) in enumerate(bolt_coords):
        t_force = bolt_forces[idx]
        b_color = '#F44336' if t_force > 0 else '#4CAF50'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-350, tp+50], mode='lines+markers', marker=dict(size=6, color=b_color), line=dict(color=b_color, width=8), name=f'Bolt B{idx+1}', showlegend=False))
        if t_force > 0:
            draw_force_vector(fig, start_pt=(bx, by, tp+50), end_pt=(bx, by, tp+50 + 80 + (t_force*1.5)), color='#D32F2F', name='Tension')

    # ลิ่มแรงกดคอนกรีต
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2], z=[0, 0, 0, 0, -50, -50, -50, -50], color='rgba(255, 152, 0, 0.6)', name='Concrete Bearing'))

    # 🔥 วาดลูกศรแรงหลัก (Global Loads) แบบกำหนดเองให้เห็นชัวร์ 100%
    draw_force_vector(fig, start_pt=(0, 0, tp+h_col+200), end_pt=(0, 0, tp+h_col), color='black', name='Pu (Axial)')
    
    if V_u > 0:
        draw_force_vector(fig, start_pt=(0, -200, tp+h_col), end_pt=(0, 0, tp+h_col), color='purple', name='Vu (Shear)')
        
    if M_u > 0:
        draw_force_vector(fig, start_pt=(0, -d/2, tp+h_col+150), end_pt=(0, -d/2, tp+h_col), color='orange', name='Mu (Comp Couple)')
        draw_force_vector(fig, start_pt=(0, d/2, tp+h_col), end_pt=(0, d/2, tp+h_col+150), color='deeppink', name='Mu (Ten Couple)')

    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))), margin=dict(l=0, r=0, b=0, t=0), height=650)
    return fig

# ================= ================= =================
# 3. INTERACTIVE CONTROL (CUSTOM BOLT COORDINATES)
# ================= ================= =================
col_ctrl, col_view = st.columns([1.1, 0.9])

with col_ctrl:
    st.markdown("<div class='step-header'>🏗️ STEP 1: หน้าตัดเหล็กและแรงประลัย (มิลลิเมตร)</div>", unsafe_allow_html=True)
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1: d = st.number_input("ลึกเสา d", min_value=100.0, value=300.0)
    with c_m2: bf = st.number_input("กว้างปีก bf", min_value=100.0, value=300.0)
    with c_m3: tw = st.number_input("หนาเอว tw", min_value=2.0, value=10.0)
    with c_m4: tf = st.number_input("หนาปีก tf", min_value=2.0, value=15.0)

    cx1, cx2, cx3 = st.columns(3)
    with cx1: p_u_kn = st.number_input("แรงกด Pu (kN)", value=500.0)
    with cx2: v_u_kn = st.number_input("แรงเฉือน Vu (kN)", value=110.0)
    with cx3: m_u_knm = st.number_input("โมเมนต์ Mu (kN-m)", value=120.0)
    fc_mpa = st.number_input("กำลังอัดตอม่อ fc' (MPa)", value=28.0)

    st.markdown("<div class='step-header'>📐 STEP 2: ขนาดแผ่นเพลต และกำหนดพิกัดโบลต์อิสระ</div>", unsafe_allow_html=True)
    c_p1, c_p2 = st.columns(2)
    with c_p1: B = st.number_input("กว้างแผ่นเพลต B (mm)", value=float(bf+150.0))
    with c_p2: N = st.number_input("ยาวแผ่นเพลต N (mm)", value=float(d+200.0))
    
    tp = THAI_PLATE_THICKNESSES_MM[st.selectbox("หนาแผ่นเพลต (mm)", list(THAI_PLATE_THICKNESSES_MM.keys()), index=4)]

    # 💡 ระบบให้คำแนะนำและให้ผู้ใช้กำหนดพิกัดโบลต์เอง (Smart Recommendation & Manual Override)
    st.markdown("**กำหนดระยะเรียงโบลต์ (Bolt Spacing):**")
    safe_sx = bf + 90.0  # ระยะแนะนำไม่ให้ชนปีกเสาซ้ายขวา
    safe_sy = d + 90.0   # ระยะแนะนำไม่ให้ชนปีกเสาบนล่าง
    
    col_s1, col_s2 = st.columns(2)
    with col_s1: 
        s_x = st.number_input("ระยะห่างระหว่างโบลต์แกน X (Sx)", min_value=50.0, value=safe_sx, help=f"แนะนำที่ > {bf+90} mm")
    with col_s2: 
        s_y = st.number_input("ระยะห่างระหว่างโบลต์แกน Y (Sy)", min_value=50.0, value=safe_sy, help=f"แนะนำที่ > {d+90} mm")

    # ตรวจสอบการชน (Clearance Check)
    if s_x < (bf + 70) or s_y < (d + 70):
        st.markdown("<div class='error-box'>⚠️ คำเตือน: ระยะโบลต์ที่คุณกำหนด ชิดเสาเหล็กมากเกินไป ประแจปอนด์อาจเข้าขันไม่ได้ หรือหัวนอตเกยรอยเชื่อมปีกเสา (แนะนำให้กว้างกว่าขนาดเสาอย่างน้อย 90 mm)</div>", unsafe_allow_html=True)

    bolt_profile = THAI_ANCHOR_BOLTS_MM[st.selectbox("ขนาดสลักเกลียว", list(THAI_ANCHOR_BOLTS_MM.keys()), index=3)]

    # คำนวณพิกัด (X, Y) จาก Sx, Sy ที่ผู้ใช้กำหนด
    hx, hy = s_x / 2.0, s_y / 2.0
    bolt_coords = [(-hx, -hy), (hx, -hy), (-hx, hy), (hx, hy)]
    num_bolts = len(bolt_coords)
    
    # คำนวณกลศาสตร์แยกหัวโบลต์
    I_y_group = sum([by**2 for (_, by) in bolt_coords])
    P_u_n, V_u_n, M_u_nmm = p_u_kn * 1000.0, v_u_kn * 1000.0, m_u_knm * 1000000.0
    
    bolt_forces = []
    for (bx, by) in bolt_coords:
        t_f = max(0.0, ((M_u_nmm * by) / I_y_group if I_y_group > 0 else 0.0) + (-P_u_n / num_bolts))
        bolt_forces.append(t_f / 1000.0)

# ================= ================= =================
# 4. DASHBOARD & RENDER
# ================= ================= =================
with col_view:
    st.markdown("### 🔍 Bolt Coordinates & Forces")
    matrix_table = []
    for idx, (bx, by) in enumerate(bolt_coords):
        matrix_table.append({
            "โบลต์": f"B{idx+1}", "พิกัด X (mm)": int(bx), "พิกัด Y (mm)": int(by), "แรงดึงที่เกิด (kN)": round(bolt_forces[idx], 1)
        })
    st.table(matrix_table)

    # 3D Render
    f_p_max = 0.65 * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    Y_length = N if ecc <= (N/6.0) else max(0.0, (N/2.0) - (P_u_n / (2.0 * B * f_p_max)))
    
    st.markdown("### 🧊 High-Visibility Vector Model")
    fig_adv = generate_bulletproof_3d(B, N, tp, d, bf, tw, tf, bolt_coords, bolt_forces, Y_length, p_u_kn, v_u_kn, m_u_knm)
    st.plotly_chart(fig_adv, use_container_width=True)
