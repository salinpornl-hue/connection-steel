# app.py
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. METRIC DATABASE & MATERIALS
# ==========================================
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

st.set_page_config(page_title="AISC-Thai Senior Connection Engine", layout="wide")
st.markdown("""
    <style>
    .step-header { background-color: #0f172a; color: white; padding: 12px 18px; border-radius: 6px; margin-top: 20px; margin-bottom: 15px; font-weight: bold; border-left: 6px solid #3b82f6; }
    .status-pass { color: #059669; font-weight: bold; }
    .status-fail { color: #dc2626; font-weight: bold; }
    .warning-box { background-color: #fef2f2; color: #b91c1c; padding: 15px; border-radius: 6px; border: 1px solid #fca5a5; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ AISC-Thai Senior Engineer Edition")
st.caption("ระบบวิเคราะห์พิกัดโบลต์อิสระรายตัว (Custom Matrix) พร้อมรอยเชื่อมและเวกเตอร์ 3D ขั้นสูง | LRFD Metric")

# ==========================================
# 2. BULLETPROOF 3D ENGINE
# ==========================================
def draw_custom_vector(fig, start_pt, end_pt, color, name, arrow_scale=60):
    fig.add_trace(go.Scatter3d(
        x=[start_pt[0], end_pt[0]], y=[start_pt[1], end_pt[1]], z=[start_pt[2], end_pt[2]],
        mode='lines', line=dict(color=color, width=10), name=name
    ))
    vec_x, vec_y, vec_z = end_pt[0]-start_pt[0], end_pt[1]-start_pt[1], end_pt[2]-start_pt[2]
    fig.add_trace(go.Cone(
        x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]],
        u=[vec_x], v=[vec_y], w=[vec_z],
        sizemode="absolute", sizeref=arrow_scale, showscale=False, colorscale=[[0, color], [1, color]], showlegend=False
    ))

def render_engineering_3d(B, N, tp, d, bf, tw, tf, df_bolts, P_u, V_u, M_u, Y_length):
    fig = go.Figure()
    h_col = 500.0 

    # Concrete & Plate
    fig.add_trace(go.Mesh3d(x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8], y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8], z=[-300, -300, -300, -300, 0, 0, 0, 0], color='lightgrey', opacity=0.15, name='Concrete'))
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#64748b', opacity=0.9, name='Base Plate'))

    # H-Beam
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#334155', name='H-Beam'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#334155', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col], color='#475569', showlegend=False))

    # Welds
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#3b82f6', width=6), name='Flange Weld'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#3b82f6', width=6), showlegend=False))

    # Bolts & Tension Vectors
    for _, row in df_bolts.iterrows():
        bx, by, t_force, b_id = row['X (mm)'], row['Y (mm)'], row['Tension (kN)'], row['Bolt ID']
        b_color = '#ef4444' if t_force > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-250, tp+40], mode='lines+markers+text', marker=dict(size=5, color=b_color), line=dict(color=b_color, width=7), text=[f" {b_id}", ""], textposition="top right", name=f'Bolt {b_id}', showlegend=False))
        
        if t_force > 0:
            draw_custom_vector(fig, start_pt=(bx, by, tp+40), end_pt=(bx, by, tp+40 + 60 + (t_force)), color='#b91c1c', name=f'Tension {b_id}', arrow_scale=30)

    # Concrete Compression Block
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2], z=[0, 0, 0, 0, -50, -50, -50, -50], color='rgba(249, 115, 22, 0.5)', name='Bearing Block'))

    # Global Loads
    draw_custom_vector(fig, start_pt=(0, 0, tp+h_col+200), end_pt=(0, 0, tp+h_col), color='black', name='Pu (Axial)')
    if V_u > 0: draw_custom_vector(fig, start_pt=(0, -200, tp+h_col), end_pt=(0, 0, tp+h_col), color='#9333ea', name='Vu (Shear)')
    if M_u > 0:
        draw_custom_vector(fig, start_pt=(0, -d/2, tp+h_col+150), end_pt=(0, -d/2, tp+h_col), color='#f59e0b', name='Mu (Comp Couple)')
        draw_custom_vector(fig, start_pt=(0, d/2, tp+h_col), end_pt=(0, d/2, tp+h_col+150), color='#ec4899', name='Mu (Ten Couple)')

    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.0))), margin=dict(l=0, r=0, b=0, t=0), height=700)
    return fig

# ==========================================
# 3. INTERACTIVE UI & CALCULATION
# ==========================================
col_ctrl, col_view = st.columns([1.1, 0.9])

with col_ctrl:
    st.markdown("<div class='step-header'>1. ข้อมูลหน้าตัดเสาและแรงประลัย (มิลลิเมตร, kN)</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    d = c1.number_input("ความลึกเสา d", value=300.0)
    bf = c2.number_input("กว้างปีก bf", value=300.0)
    tw = c3.number_input("หนาเอว tw", value=10.0)
    tf = c4.number_input("หนาปีก tf", value=15.0)
    
    cx1, cx2, cx3, cx4 = st.columns(4)
    p_u_kn = cx1.number_input("แรงกด Pu", value=500.0)
    v_u_kn = cx2.number_input("แรงเฉือน Vu", value=110.0)
    m_u_knm = cx3.number_input("โมเมนต์ Mu", value=120.0)
    fc_mpa = cx4.number_input("กำลังคอนกรีต fc'", value=28.0)

    st.markdown("<div class='step-header'>2. มิติแผ่นฐานเพลต และขนาดสลักเกลียว</div>", unsafe_allow_html=True)
    cp1, cp2, cp3, cp4 = st.columns(4)
    B = cp1.number_input("ความกว้าง B", value=float(bf+150))
    N = cp2.number_input("ความยาว N", value=float(d+150))
    tp = THAI_PLATE_THICKNESSES_MM[cp3.selectbox("ความหนา tp", list(THAI_PLATE_THICKNESSES_MM.keys()), index=4)]
    bolt_profile = THAI_ANCHOR_BOLTS_MM[cp4.selectbox("ขนาดโบลต์", list(THAI_ANCHOR_BOLTS_MM.keys()), index=3)]

    st.markdown("<div class='step-header'>3. กำหนดพิกัดโบลต์รายตัว (อิสระ 100%)</div>", unsafe_allow_html=True)
    st.caption("สามารถเพิ่ม/ลบ/แก้ไขพิกัด (X,Y) ของโบลต์บนแผ่นเพลตได้อิสระ โดยจุด (0,0) คือจุดศูนย์กลางเสา")
    
    # Smart Defaults
    default_x, default_y = (bf/2) + 45.0, (d/2) + 45.0
    initial_bolts = pd.DataFrame({
        "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
        "X (mm)": [-default_x, default_x, -default_x, default_x, -default_x, default_x],
        "Y (mm)": [default_y, default_y, 0.0, 0.0, -default_y, -default_y]
    })
    
    # เปิดให้ผู้ใช้ Edit Dataframe สดๆ
    edited_df = st.data_editor(initial_bolts, num_rows="dynamic", use_container_width=True)
    num_bolts = len(edited_df)

    # 🛑 Individual Clearance Guardrail
    clearance_errors = []
    for _, row in edited_df.iterrows():
        bx, by, bid = row['X (mm)'], row['Y (mm)'], row['Bolt ID']
        # ถ้าระยะตกอยู่ภายในโซนเสา หรือใกล้เกินไป
        dist_x_to_flange = abs(bx) - (bf/2)
        dist_y_to_flange = abs(by) - (d/2)
        dist_x_to_web = abs(bx) - (tw/2)
        
        if (abs(by) <= d/2 + 40) and (abs(bx) <= bf/2 + 40): # อยู่ใกล้โซน H-Beam
            if dist_x_to_web < 45 and dist_y_to_flange < 45:
                clearance_errors.append(f"<b>{bid}:</b> พิกัด ({bx}, {by}) ชิดเอว/ปีกเสาเกินไป ประแจขันไม่ได้!")
    
    if clearance_errors:
        err_msg = "<br>".join(clearance_errors)
        st.markdown(f"<div class='warning-box'>⚠️ <b>พบระยะติดตั้งขัดแย้งหน้างาน!</b><br>{err_msg}</div>", unsafe_allow_html=True)

    st.markdown("<div class='step-header'>4. ขีดจำกัดรอยเชื่อมรอบเสาเหล็ก</div>", unsafe_allow_html=True)
    weld_size_mm = st.slider("ขนาดรอยเชื่อมขา Fillet (mm)", 3, 16, 8)

# ==========================================
# 4. ENGINEERING MECHANICS & METRICS
# ==========================================
with col_view:
    # ⚙️ Elastic Bolt Group Calculation
    P_u_n, V_u_n, M_u_nmm = p_u_kn * 1000.0, v_u_kn * 1000.0, m_u_knm * 1000000.0
    I_y_group = sum(edited_df['Y (mm)']**2) if num_bolts > 0 else 1.0
    
    tensions = []
    for y in edited_df['Y (mm)']:
        t_f = ((M_u_nmm * y) / I_y_group) + (-P_u_n / num_bolts)
        tensions.append(max(0.0, t_f / 1000.0))
    edited_df['Tension (kN)'] = tensions

    # ⚙️ Base Plate & Bearing
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    Y_length = N if ecc <= (N/6.0) else max(0.0, (N/2.0) - (P_u_n / (2.0 * B * f_p_max)))
    bearing_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
    
    m = (N - 0.95 * d) / 2.0
    n_plate = (B - 0.80 * bf) / 2.0
    t_req = max(m, n_plate) * math.sqrt((2.0 * bearing_actual) / (0.90 * 245.0))

    # ⚙️ Weld Calculations
    l_f_weld = 4.0 * bf
    l_w_weld = 2.0 * (d - 2*tf)
    weld_cap = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0
    weld_demand = max(
        ((P_u_n / (l_f_weld + l_w_weld)) + (M_u_nmm / (bf * (d - tf)))) / 1000.0,
        (V_u_n / l_w_weld) / 1000.0 if l_w_weld > 0 else 0
    )

    # ⚙️ Capacities
    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area_as"]) / 1000.0
    bolt_v_cap = (0.75 * bolt_profile["F_nv"] * bolt_profile["area_as"]) / 1000.0
    shear_per_bolt = v_u_kn / num_bolts if num_bolts > 0 else 0

    st.markdown("### 📊 AISC Safety Matrix")
    report = [
        {"รายการ": "แรงกดคอนกรีตฐานราก", "ใช้จริง": f"{bearing_actual:.1f} MPa", "รับได้": f"{f_p_max:.1f} MPa", "สถานะ": "PASS" if bearing_actual<=f_p_max else "FAIL"},
        {"รายการ": "ความหนาแผ่นเพลต", "ใช้จริง": f"{t_req:.1f} mm", "รับได้": f"{tp:.1f} mm", "สถานะ": "PASS" if t_req<=tp else "FAIL"},
        {"รายการ": "แรงเฉือนรอยเชื่อม", "ใช้จริง": f"{weld_demand:.2f} kN/mm", "รับได้": f"{weld_cap:.2f} kN/mm", "สถานะ": "PASS" if weld_demand<=weld_cap else "FAIL"},
        {"รายการ": "แรงดึงโบลต์สูงสุด", "ใช้จริง": f"{max_t_actual:.1f} kN", "รับได้": f"{bolt_t_cap:.1f} kN", "สถานะ": "PASS" if max_t_actual<=bolt_t_cap else "FAIL"},
        {"รายการ": "แรงเฉือนโบลต์เฉลี่ย", "ใช้จริง": f"{shear_per_bolt:.1f} kN", "รับได้": f"{bolt_v_cap:.1f} kN", "สถานะ": "PASS" if shear_per_bolt<=bolt_v_cap else "FAIL"},
    ]
    st.dataframe(pd.DataFrame(report), use_container_width=True)

    st.markdown("### 🧊 Custom Bolt-Matrix 3D Render")
    fig_adv = render_engineering_3d(B, N, tp, d, bf, tw, tf, edited_df, p_u_kn, v_u_kn, m_u_knm, Y_length)
    st.plotly_chart(fig_adv, use_container_width=True)
