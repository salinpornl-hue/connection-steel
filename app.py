# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. METRIC DATABASE & HIGH-FIDELITY DESIGN SPEC
# ================= ================= =================
THAI_PLATE_THICKNESSES_MM = {
    "12 mm": 12.0, "16 mm": 16.0, "19 mm": 19.0, "22 mm": 22.0, 
    "25 mm": 25.0, "28 mm": 28.0, "32 mm": 32.0, "38 mm": 38.0, "50 mm": 50.0
}

THAI_ANCHOR_BOLTS_MM = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area_as": 157.0, "F_nt": 300.0, "F_nv": 180.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area_as": 245.0, "F_nt": 300.0, "F_nv": 180.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area_as": 353.0, "F_nt": 300.0, "F_nv": 180.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area_as": 561.0, "F_nt": 600.0, "F_nv": 360.0},
    "M36 (Grade 8.8)": {"dia": 36.0, "area_as": 817.0, "F_nt": 600.0, "F_nv": 360.0}
}

st.set_page_config(page_title="AISC-Thai Professional Connection Engine", layout="wide")
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .weld-label { font-weight: bold; color: #1e88e5; }
    .bolt-matrix { font-family: monospace; background-color: #f5f5f5; padding: 5px; border-radius: 3px; }
    .step-header { background-color: #0d47a1; color: white; padding: 10px 15px; border-radius: 4px; margin-top: 18px; margin-bottom: 12px; font-weight: bold; font-size: 1.05rem; }
    .error-box { background-color: #ffebee; color: #b71c1c; padding: 12px; border-radius: 4px; border-left: 6px solid #e53935; margin-bottom: 10px; font-size: 0.95rem; }
    .pass-tag { color: #2e7d32; font-weight: bold; }
    .fail-tag { color: #c62828; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 AISC-Thai Advanced Bolt-Matrix Connection Engine")
st.caption("ระบบคำนวณกลศาสตร์พิกัดโบลต์รายตัว (Individual Bolt-Matrix) และเวกเตอร์แรงประลัยเด่นชัดสเกลสูง | AISC 360 LRFD")

# ================= ================= =================
# 2. HIGH-VISIBILITY 3D GRAPHICS ENGINE (GIANT VECTORS)
# ================= ================= =================
def generate_advanced_3d(B, N, tp, d, bf, tw, tf, bolt_coords, bolt_forces, Y_length, P_u, V_u, M_u):
    fig = go.Figure()
    h_col = 600.0  # ความสูงเสาเหล็กจำลอง (mm)

    # 1. คอนกรีตตอม่อฐานราก
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-450, -450, -450, -450, 0, 0, 0, 0],
        color='rgb(220, 220, 220)', opacity=0.12, name='Concrete Pedestal'
    ))

    # 2. แผ่นเหล็กฐานเพลต (Base Plate)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='rgb(90, 100, 110)', opacity=0.85, name='Base Plate'
    ))

    # 3. หน้าตัดเสาเหล็ก H-Beam Solid Component
    # ปีกเสาล่าง (-Y)
    fig.add_trace(go.Mesh3d(
        x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2],
        y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(45, 55, 70)', opacity=0.9, name='Column Flanges'
    ))
    # ปีกเสาบน (+Y)
    fig.add_trace(go.Mesh3d(
        x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2],
        y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(45, 55, 70)', opacity=0.9, showlegend=False
    ))
    # เอวเสา (Web)
    fig.add_trace(go.Mesh3d(
        x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2],
        y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(65, 75, 90)', opacity=0.9, name='Column Web'
    ))

    # 4. แนวรอยเชื่อมพอกรอบหน้าตัดเสา
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='blue', width=7), name='Flange Weld Line'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='blue', width=7), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[-tw/2-1, -tw/2-1], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='cyan', width=5), name='Web Weld Line'))
    fig.add_trace(go.Scatter3d(x=[tw/2+1, tw/2+1], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='cyan', width=5), showlegend=False))

    # 5. การพลอตกลุ่มโบลต์ตามพิกัดจริงและเวกเตอร์แรงดึงรายตัว (Individual Vectors)
    for idx, (bx, by) in enumerate(bolt_coords):
        t_force = bolt_forces[idx]
        b_color = 'rgb(244, 67, 54)' if t_force > 0 else 'rgb(76, 175, 80)'
        
        # แสดงแท่งสลักเกลียวฝังลึก
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-350, tp+50], mode='lines+markers+text',
            marker=dict(size=6, color=b_color), line=dict(color=b_color, width=7),
            text=[f"B{idx+1}" if z_p > 0 else "" for z_p in [-350, tp+50]], textposition="top center",
            name=f'Anchor Bolt B{idx+1}', showlegend=False
        ))
        
        # 🔴 เพิ่มลูกศรแรงดึงงัดหัวโบลต์แบบเด่นชัดพิเศษขยายขนาดใหญ่ (Giant Single Bolt Tension)
        if t_force > 0:
            arrow_len = 50.0 + (t_force * 2.0)  # สเกลความยาวแปรผันตามแรงจริง
            fig.add_trace(go.Cone(
                x=[bx], y=[by], z=[tp+50], u=[0], v=[0], w=[arrow_len],
                sizemode="absolute", sizeref=35, showscale=False, 
                colorscale=[[0,'rgb(211, 47, 47)'],[1,'rgb(211, 47, 47)']], name='Bolt Tension Vector'
            ))

    # 6. บล็อกสัมผัสแรงกดคอนกรีตสีส้มสดสะท้อนแสง
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2],
            z=[0, 0, 0, 0, -60, -60, -60, -60],
            color='rgba(255, 102, 0, 0.6)', name='Bearing Stress Compression Block'
        ))

    # 7. 🔥 [RE-ENGINEERED] ขยายขนาดและสีเวกเตอร์น้ำหนักบรรทุกหลัก (GLOBAL GIANT VECTORS)
    # 🖤 ลูกศรแรงกดหัวเสาตัวยักษ์สีดำสนิท พุ่งดิ่งลงปะทะแผ่นเพลต
    fig.add_trace(go.Cone(
        x=[0], y=[0], z=[tp+h_col+180], u=[0], v=[0], w=[-150],
        sizemode="absolute", sizeref=70, showscale=False, 
        colorscale=[[0,'black'],[1,'black']], name='Pu: Axial Compression Load'
    ))
    
    # 💜 ลูกศรแรงเฉือนตัวยาวสีม่วงสด พุ่งขนานตัดเฉือนระนาบรอยเชื่อม
    if V_u > 0:
        fig.add_trace(go.Cone(
            x=[0], y=[-150], z=[tp+h_col], u=[0], v=[180], w=[0],
            sizemode="absolute", sizeref=60, showscale=False, 
            colorscale=[[0,'rgb(156, 39, 176)'],[1,'rgb(156, 39, 176)']], name='Vu: Shear Load'
        ))
    
    # 💛+💖 ลูกศรงัดแรงคู่ควบแทนโมเมนต์ดัดแบบโอเวอร์สเกลให้เห็นทิศทางการหมุนชัดเจน
    if M_u > 0:
        # ฝั่งซ้ายกดลงกระแทกแผ่นเพลต (Compression side)
        fig.add_trace(go.Cone(
            x=[0], y=[-d/2], z=[tp+h_col+100], u=[0], v=[0], w=[-100], 
            sizemode="absolute", sizeref=45, showscale=False, 
            colorscale=[[0,'rgb(255, 152, 0)'],[1,'rgb(255, 152, 0)']], name='Mu Couple: Compression'
        ))
        # ฝั่งขวางัดพุ่งขึ้นฟ้า ดึงกลุ่มโบลต์หลุด (Tension side)
        fig.add_trace(go.Cone(
            x=[0], y=[d/2], z=[tp+h_col], u=[0], v=[0], w=[100], 
            sizemode="absolute", sizeref=45, showscale=False, 
            colorscale=[[0,'rgb(233, 30, 99)'],[1,'rgb(233, 30, 99)']], name='Mu Couple: Tension'
        ))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='X (Width-mm)', backgroundcolor="rgb(250, 250, 250)", gridcolor="white"),
            yaxis=dict(title='Y (Length-mm)', backgroundcolor="rgb(250, 250, 250)", gridcolor="white"),
            zaxis=dict(title='Z (Height-mm)', backgroundcolor="rgb(240, 240, 240)", gridcolor="white"),
            aspectmode='data', camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=650
    )
    return fig

# ================= ================= =================
# 3. INTERACTIVE CONTROL PANEL (METRIC UNITS)
# ================= ================= =================
col_ctrl, col_view = st.columns([1.1, 0.9])

with col_ctrl:
    st.markdown("<div class='step-header'>🏗️ STEP 1: ป้อนรายละเอียดมิติเหล็กและน้ำหนักบรรทุกประลัย</div>", unsafe_allow_html=True)
    
    thai_steel_preset = st.selectbox("เลือกหน้าตัดเสาเหล็ก H-Beam มาตรฐาน มอก.:", [
        "Custom (กำหนดเอง)", "H 200x200x8x12 mm", "H 250x250x9x14 mm", "H 300x300x10x15 mm", "H 400x400x13x21 mm"
    ], index=3)
    
    d, bf, tw, tf = 300.0, 300.0, 10.0, 15.0
    if "200x200" in thai_steel_preset: d, bf, tw, tf = 200.0, 200.0, 8.0, 12.0
    elif "250x250" in thai_steel_preset: d, bf, tw, tf = 250.0, 250.0, 9.0, 14.0
    elif "400x400" in thai_steel_preset: d, bf, tw, tf = 400.0, 400.0, 13.0, 21.0

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1: d = st.number_input("ลึกเสา d (mm)", min_value=50.0, value=d)
    with c_m2: bf = st.number_input("กว้างปีก bf (mm)", min_value=50.0, value=bf)
    with c_m3: tw = st.number_input("หนาเอว tw (mm)", min_value=2.0, value=tw)
    with c_m4: tf = st.number_input("หนาปีก tf (mm)", min_value=2.0, value=tf)

    cx1, cx2, cx3 = st.columns(3)
    with cx1: p_u_kn = st.number_input("แรงกดประลัย Pu (kN)", min_value=1.0, value=500.0)
    with cx2: v_u_kn = st.number_input("แรงเฉือนประลัย Vu (kN)", min_value=0.0, value=110.0)
    with cx3: m_u_knm = st.number_input("โมเมนต์ดัดประลัย Mu (kN-m)", min_value=0.0, value=120.0)
    
    fc_mpa = st.number_input("กำลังอัดคอนกรีตตอม่อ fc' (MPa)", min_value=15.0, value=28.0)

    st.markdown("<div class='step-header'>📐 STEP 2: ขนาดแผ่นเหล็กเพลต และตัวควบคุมสลักเกลียวสลับแถว</div>", unsafe_allow_html=True)
    
    c_p1, c_p2 = st.columns(2)
    with c_p1: B = st.number_input("กว้างแผ่นเพลตจริง B (mm)", min_value=bf+50.0, value=450.0)
    with c_p2: N = st.number_input("ยาวแผ่นเพลตจริง N (mm)", min_value=d+50.0, value=500.0)

    # พารามิเตอร์การจัดระยะโบลต์แบบละเอียดจริงหน้างาน
    c_g1, c_g2 = st.columns(2)
    with c_g1: edge_x = st.number_input("ระยะร่นโบลต์จากขอบซ้าย-ขวา Ex (mm)", min_value=30.0, value=65.0)
    with c_g2: edge_y = st.number_input("ระยะร่นโบลต์จากขอบบน-ล่าง Ey (mm)", min_value=30.0, value=65.0)

    # สรุปเช็กระยะชนประเจขัน (Geometrical Bolt Clearance)
    bolt_y_pos = (N / 2.0) - edge_y
    clearance = bolt_y_pos - (d / 2.0)
    if clearance < 45.0:
        st.markdown(f"<div class='error-box'>⚠️ ระยะขัดแย้งเชิงมิติ: หัวนอตห่างปีกเสาเพียง {round(clearance,1)} mm เครื่องมือขันประกอบไม่ได้! (ต้องการอย่างน้อย 45 mm)</div>", unsafe_allow_html=True)

    selected_thickness_label = st.selectbox("เลือกความหนาเหล็กแผ่นฐานเพลต (mm):", list(THAI_PLATE_THICKNESSES_MM.keys()), index=4)
    tp = THAI_PLATE_THICKNESSES_MM[selected_thickness_label]

    st.markdown("<div class='step-header'>🔩 STEP 3: ระบบจัดรูปแบบพิกัดกลุ่มโบลต์แบบละเอียด (Bolt-Matrix Allocation)</div>", unsafe_allow_html=True)
    
    bolt_pattern = st.radio("เลือกรูปแบบการจัดวางกลุ่มโบลต์:", ["4-Corner (4 ตัวมุมเพลต)", "6-Grid Perimeter (6 ตัวรอบเพลต)", "8-Matrix Dynamic (8 ตัวเรียงแถวสมมาตร)"])
    selected_bolt = st.selectbox("ระบุขนาดและเกรดสลักเกลียว มอก.:", list(THAI_ANCHOR_BOLTS_MM.keys()), index=3)
    bolt_profile = THAI_ANCHOR_BOLTS_MM[selected_bolt]

    # สร้างพิกัด (X, Y) ของโบลต์แต่ละตัวอย่างละเอียดตามแบบวิศวกรรมจริง
    lx, ly = (B/2) - edge_x, (N/2) - edge_y
    if "4-Corner" in bolt_pattern:
        bolt_coords = [(-lx, -ly), (lx, -ly), (-lx, ly), (lx, ly)]
    elif "6-Grid" in bolt_pattern:
        bolt_coords = [(-lx, -ly), (lx, -ly), (-lx, 0), (lx, 0), (-lx, ly), (lx, ly)]
    else:
        bolt_coords = [(-lx, -ly), (0, -ly), (lx, -ly), (-lx, ly), (0, ly), (lx, ly), (-lx, 0), (lx, 0)]

    num_bolts = len(bolt_coords)
    
    # ⚙️ กลศาสตร์การคำนวณสากล LRFD กระจายโมเมนต์สู่กลุ่มโบลต์รายตัวจริง
    # หาคุณสมบัติหน้าตัดรวมของกลุ่มโบลต์ (Bolt Group Elastic Analysis)
    I_y_group = sum([by**2 for (_, by) in bolt_coords])
    
    P_u_n = p_u_kn * 1000.0
    V_u_n = v_u_kn * 1000.0
    M_u_nmm = m_u_knm * 1000000.0
    
    # วิเคราะห์หาแรงดึงสุทธิรายตัว
    bolt_forces = []
    for (bx, by) in bolt_coords:
        # แรงดึงจากโมเมนต์ลบด้วยแรงกดสม่ำเสมอจากแกน
        t_from_m = (M_u_nmm * by) / I_y_group if I_y_group > 0 else 0.0
        t_from_p = -P_u_n / num_bolts
        total_f = t_from_m + t_from_p
        bolt_forces.append(max(0.0, total_f / 1000.0)) # เก็บค่าเฉพาะแรงดึง (kN)
        
    shear_per_bolt_kn = v_u_kn / num_bolts

    st.markdown("<div class='step-header'>⚡ STEP 4: ขีดจำกัดรอยเชื่อมรอบเสาเหล็กปะทะเนื้อเหล็กเดิม (Weld vs. Base Metal)</div>", unsafe_allow_html=True)
    weld_size_mm = st.slider("ระบุขนาดรอยเชื่อมจริงขา fillet (mm):", min_value=3, max_value=16, value=8)
    
    # คำนวณความแข็งแรงรอยเชื่อมและเนื้อเหล็กคู่ต่อ
    length_flange_weld = 4.0 * bf
    length_web_weld = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0
    
    weld_cap_per_mm = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0
    # 🛑 เช็กความสอดคล้องความพังเนื้อเหล็กฐาน (Base Metal Base Yielding Check) ตามมาตรฐานกำหนด
    base_metal_shear_yield_cap = 0.90 * 0.60 * 245.0 * tf / 1000.0 # kN/mm

    weld_demand_flange = ((P_u_n / (length_flange_weld + length_web_weld)) + (M_u_nmm / (bf * (d - tf)))) / 1000.0
    weld_demand_web = (V_u_n / length_web_weld) / 1000.0

# ================= ================= =================
# 4. COMPREHENSIVE VISUAL DIAGNOSTICS & DASHBOARD
# ================= ================= =================
with col_view:
    st.markdown("### 📊 Bolt-Matrix Detailed Mechanics")
    st.caption("แจกแจงค่าพิกัดจุดศูนย์กลางเชิงกล และแรงเค้นประลัยดึงงัดรายหัวโบลต์จริง")
    
    matrix_table = []
    for idx, (bx, by) in enumerate(bolt_coords):
        t_f = bolt_forces[idx]
        matrix_table.append({
            "รหัสโบลต์": f"Anchor Bolt B{idx+1}",
            "พิกัด X (mm)": f"{int(bx)}",
            "พิกัด Y (mm)": f"{int(by)}",
            "แรงดึงประลัยที่ได้รับจริง": f"{round(t_f, 1)} kN",
            "สถานะแรง": "🔴 TENSION" if t_f > 0 else "🟢 CLAMPED/COMP."
        })
    st.table(matrix_table)

    # ตรวจสอบขีดจำกัดวิศวกรรมจุดต่อแบบครบวงจร
    st.markdown("### 🔍 Multi-Component Safety Matrix")
    
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    Y_length = N if ecc <= (N/6.0) else max(0.0, (N/2.0) - (P_u_n / (2.0 * B * f_p_max)))
    bearing_stress_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
    
    m = (N - 0.95 * d) / 2.0
    t_req = m * math.sqrt((2.0 * bearing_stress_actual) / (0.90 * 245.0))

    util_bearing = (bearing_stress_actual / f_p_max) * 100
    util_plate = (t_req / tp) * 100
    util_weld_f = (weld_demand_flange / weld_cap_per_mm) * 100
    util_bolt_max_t = (max(bolt_forces) / ((0.75 * bolt_profile["F_nt"] * bolt_profile["area_as"])/1000.0)) * 100 if max(bolt_forces)>0 else 0

    status_weld_base = "🟢 PASS (เหล็กฐานไม่ฉีกขาด)" if weld_cap_per_mm <= base_metal_shear_yield_cap else "⚠️ WARNING (รอยเชื่อมหนาเกินไป เนื้อเหล็กเสาจะฉีกก่อน)"

    report_rows = [
        {"ด่านทดสอบความปลอดภัย": "1. แรงกดปะทะหน้าคอนกรีตฐานราก", "อัตราส่วนแรงเค้น %": f"{round(util_bearing, 1)}%", "ผลทดสอบ": "ผ่าน" if util_bearing<=100 else "วิบัติ"},
        {"ด่านทดสอบความปลอดภัย": "2. ความหนาเหล็กแผ่นฐานเพลต", "อัตราส่วนแรงเค้น %": f"{round(util_plate, 1)}%", "ผลทดสอบ": "ผ่าน" if util_plate<=100 else "วิบัติ"},
        {"ด่านทดสอบความปลอดภัย": "3. เนื้อรอยเชื่อมพอกปีกเสาเหล็ก", "อัตราส่วนแรงเค้น %": f"{round(util_weld_f, 1)}%", "ผลทดสอบ": "ผ่าน" if util_weld_f<=100 else "วิบัติ"},
        {"ด่านทดสอบความปลอดภัย": "4. แรงดึงตัวโบลต์ตัวที่วิกฤตที่สุด", "อัตราส่วนแรงเค้น %": f"{round(util_bolt_max_t, 1)}%", "ผลทดสอบ": "ผ่าน" if util_bolt_max_t<=100 else "วิบัติ"},
    ]
    st.table(report_rows)
    st.markdown(f"**สมดุลรอยเชื่อมปะทะเนื้อเหล็กเดิม:** {status_weld_base}")

    st.markdown("---")
    st.markdown("### 🧊 High-Visibility Multi-Vector 3D Structural Model")
    st.caption("ระบบแสดงเวกเตอร์แรงหลักสเกลใหญ่พิเศษเพื่อวิเคราะห์ทิศทาง: แรงกดหลัก Pu (ดำดิ่ง), แรงเฉือนหลัก Vu (ม่วงแนวนอน), โมเมนต์คู่ควบดัดหัวเสา Mu (ส้มคว่ำ/ชมพูหงาย) และแรงดึงงัดรายหัวโบลต์ (ลูกศรแดงแยกตระง่าน)")
    
    # เรียกฟังก์ชันโมเดล 3 มิติแสดงเวกเตอร์ขนาดใหญ่
    fig_adv = generate_advanced_3d(B, N, tp, d, bf, tw, tf, bolt_coords, bolt_forces, Y_length, p_u_kn, v_u_kn, m_u_knm)
    st.plotly_chart(fig_adv, use_container_width=True)
