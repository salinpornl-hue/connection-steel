# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. DATABASE & THAI COMMERCIAL METRIC CONVERSION
# ================= ================= =================
THAI_PLATE_THICKNESSES = {
    "12 mm (~1/2\")": 12.0, "16 mm (~5/8\")": 16.0, "19 mm (~3/4\")": 19.0,
    "22 mm (~7/8\")": 22.0, "25 mm (~1\")": 25.0, "28 mm (~1-1/8\")": 28.0,
    "32 mm (~1-1/4\")": 32.0, "38 mm (~1-1/2\")": 38.0, "50 mm (~2\")": 50.0
}

THAI_ANCHOR_BOLTS = {
    "M16 (Grade 4.6)": {"dia_in": 0.630, "area_in2": 0.312, "F_nt": 43.5, "F_nv": 27.0},
    "M20 (Grade 4.6)": {"dia_in": 0.787, "area_in2": 0.487, "F_nt": 43.5, "F_nv": 27.0},
    "M24 (Grade 4.6)": {"dia_in": 0.945, "area_in2": 0.701, "F_nt": 43.5, "F_nv": 27.0},
    "M30 (Grade 4.6)": {"dia_in": 1.181, "area_in2": 1.096, "F_nt": 43.5, "F_nv": 27.0},
    "M36 (Grade 4.6)": {"dia_in": 1.417, "area_in2": 1.577, "F_nt": 43.5, "F_nv": 27.0}
}

st.set_page_config(page_title="AISC-Thai Expert Connection Engine", layout="wide")
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .card-critical { background-color: #fff3r0; border-left: 6px solid #d9534f; padding: 10px; border-radius: 4px; }
    .weld-label { font-weight: bold; color: #0275d8; }
    .bolt-tension { color: #d9534f; font-weight: bold; }
    .bolt-compression { color: #5cb85c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ AISC-Thai High-Fidelity Connection Engine")
st.caption("ระบบวิเคราะห์แยกชิ้นส่วนรอยเชื่อมปีก-เอว และพฤติกรรมกลศาสตร์แรงดึงหัวโบลต์รายตัว | AISC 360-16 LRFD")

# ================= ================= =================
# 2. ULTRA-DETAILED 3D MESH GENERATION (HIGH FIDELITY)
# ================= ================= =================
def generate_high_fidelity_3d(B, N, tp_in, d_in, bf_in, tw_in, tf_in, num_anchors, Y_length, tension_per_bolt, edge_g=2.0):
    fig = go.Figure()

    # 1. คอนกรีตตอม่อโปร่งแสง (Translucent Concrete Pedestal)
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-16, -16, -16, -16, 0, 0, 0, 0],
        color='lightgrey', opacity=0.2, name='Concrete Pedestal', showlegend=True
    ))

    # 2. แผ่นฐานเหล็กหนาจริง (Solid Steel Base Plate)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp_in, tp_in, tp_in, tp_in],
        color='rgb(90, 100, 110)', opacity=0.9, name='Base Plate'
    ))

    # 3. การสร้างหน้าตัดเสา H-Beam แบบ 3D Solid Volumes แยกปีกและเอวเสาชัดเจน
    h_col = 18.0 # ความยาวเสาโชว์ในโมเดล
    # ปีกเสาฝั่งซ้าย (Left Flange)
    fig.add_trace(go.Mesh3d(
        x=[-d_in/2, -d_in/2+tf_in, -d_in/2+tf_in, -d_in/2, -d_in/2, -d_in/2+tf_in, -d_in/2+tf_in, -d_in/2],
        y=[-bf_in/2, -bf_in/2, bf_in/2, bf_in/2, -bf_in/2, -bf_in/2, bf_in/2, bf_in/2],
        z=[tp_in, tp_in, tp_in, tp_in, tp_in+h_col, tp_in+h_col, tp_in+h_col, tp_in+h_col],
        color='rgb(50, 55, 65)', opacity=0.95, name='Column Flanges'
    ))
    # ปีกเสาฝั่งขวา (Right Flange)
    fig.add_trace(go.Mesh3d(
        x=[d_in/2-tf_in, d_in/2, d_in/2, d_in/2-tf_in, d_in/2-tf_in, d_in/2, d_in/2, d_in/2-tf_in],
        y=[-bf_in/2, -bf_in/2, bf_in/2, bf_in/2, -bf_in/2, -bf_in/2, bf_in/2, bf_in/2],
        z=[tp_in, tp_in, tp_in, tp_in, tp_in+h_col, tp_in+h_col, tp_in+h_col, tp_in+h_col],
        color='rgb(50, 55, 65)', opacity=0.95, showlegend=False
    ))
    # เอวเสาตรงกลาง (Web)
    fig.add_trace(go.Mesh3d(
        x=[-d_in/2+tf_in, d_in/2-tf_in, d_in/2-tf_in, -d_in/2+tf_in, -d_in/2+tf_in, d_in/2-tf_in, d_in/2-tf_in, -d_in/2+tf_in],
        y=[-tw_in/2, -tw/2, tw_in/2, tw_in/2, -tw_in/2, -tw_in/2, tw_in/2, tw_in/2],
        z=[tp_in, tp_in, tp_in, tp_in, tp_in+h_col, tp_in+h_col, tp_in+h_col, tp_in+h_col],
        color='rgb(70, 75, 85)', opacity=0.95, name='Column Web'
    ))

    # 4. แสดงรอยเชื่อมแยกสี: ปีกสีน้ำเงินเอวสีฟ้า (Discrete Weld Lines Visualization)
    # รอยเชื่อมปีกนอก
    fig.add_trace(go.Scatter3d(x=[-d_in/2, -d_in/2], y=[-bf_in/2, bf_in/2], z=[tp_in+0.05, tp_in+0.05], mode='lines', line=dict(color='blue', width=6), name='Flange Weld'))
    fig.add_trace(go.Scatter3d(x=[d_in/2, d_in/2], y=[-bf_in/2, bf_in/2], z=[tp_in+0.05, tp_in+0.05], mode='lines', line=dict(color='blue', width=6), showlegend=False))
    # รอยเชื่อมเอวเสา (Web Weld)
    fig.add_trace(go.Scatter3d(x=[-d_in/2+tf_in, d_in/2-tf_in], y=[-tw_in/2-0.02, -tw_in/2-0.02], z=[tp_in+0.05, tp_in+0.05], mode='lines', line=dict(color='cyan', width=5), name='Web Weld'))
    fig.add_trace(go.Scatter3d(x=[-d_in/2+tf_in, d_in/2-tf_in], y=[tw_in/2+0.02, tw_in/2+0.02], z=[tp_in+0.05, tp_in+0.05], mode='lines', line=dict(color='cyan', width=5), showlegend=False))

    # 5. พิกัดและการแสดงผลสลักเกลียวฝังแบบจำแนกสถานะแรง (Tension vs Compression Bolts)
    ex, ey = (B/2) - edge_g, (N/2) - edge_g
    if num_anchors == 4: coords = [(-ex, -ey), (-ex, ey), (ex, -ey), (ex, ey)] # เรียงจากซ้ายไปขวา
    elif num_anchors == 6: coords = [(-ex, -ey), (-ex, ey), (0, -ey), (0, ey), (ex, -ey), (ex, ey)]
    else: coords = [(-ex, -ey), (-ex, ey), (0, -ey), (0, ey), (ex, -ey), (ex, ey), (-ex, 0), (ex, 0)]

    for idx, (bx, by) in enumerate(coords):
        # วิเคราะห์ทิศทางแรงดึง: ถ้ายื่นไปฝั่งค่าลบของพิกัด Y (ฝั่งที่โดนโมเมนต์ดัดงัดขึ้น) จะเกิดแรงดึง
        is_tension_side = True if by > 0 else False # อ้างอิงทิศทางโมเมนต์พลิกคว่ำ
        bolt_color = 'rgb(240, 50, 50)' if (is_tension_side and tension_per_bolt > 0) else 'rgb(50, 200, 80)'
        bolt_name = 'Anchor (Tension)' if (is_tension_side and tension_per_bolt > 0) else 'Anchor (Clamping/Comp.)'
        
        # วาดตัวโบลต์
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-12, tp_in+2], mode='lines+markers',
            marker=dict(size=4, color=bolt_color), line=dict(color=bolt_color, width=7),
            name=bolt_name, showlegend=True if idx in [0, 2] else False
        ))
        
        # ใส่ลูกศรเวกเตอร์แรงดึง (3D Cones) พุ่งขึ้นจากหัวโบลต์เฉพาะตัวที่รับแรงดึงจริง!
        if is_tension_side and tension_per_bolt > 0:
            fig.add_trace(go.Cone(
                x=[bx], y=[by], z=[tp_in+2], u=[0], v=[0], w=[tension_per_bolt*0.15 + 2],
                sizemode="absolute", sizeref=2, showscale=False, colorscale=[[0,'red'],[1,'red']], name='Tension Force Vector'
            ))

    # 6. บล็อกลิ่มแรงกดคอนกรีตแบบ 3D Solid Prism (Solid Compression Block)
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2],
            z=[0, 0, 0, 0, -2.5, -2.5, -2.5, -2.5],
            color='rgba(255, 140, 0, 0.6)', name='Concrete Bearing Volume'
        ))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='B (Width-X) [in]'), yaxis=dict(title='N (Length-Y) [in]'), zaxis=dict(title='Z [in]'),
            aspectmode='data', camera=dict(eye=dict(x=1.4, y=-1.4, z=1.1))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=580
    )
    return fig

# ================= ================= =================
# 3. INTERACTIVE SIDE-BY-SIDE DESIGN ENGINE
# ================= ================= =================
col_ctrl, col_view = st.columns([1.2, 0.8])

with col_ctrl:
    # -------------------------------------------------
    # STEP 1: DETAILED H-BEAM PROFILE (METRIC INPUT)
    # -------------------------------------------------
    st.markdown("<div class='step-header'>📍 STEP 1: ป้อนขนาดมิติเสาเหล็ก H-Beam โดยละเอียด (หน่วย มม.)</div>", unsafe_allow_html=True)
    
    # พรีเซ็ตขนาดเหล็กไวด์แฟลงก์/เอชบีมยอดนิยมในไทยตาม มอก. 1227-2558
    thai_steel_preset = st.selectbox("เลือกมิติเสา H-Beam มาตรฐานไทยด่วน หรือป้อนค่าเองด้านล่าง:", [
        "Custom (กำหนดเอง)", "H 200x200x8x12 mm", "H 250x250x9x14 mm", "H 300x300x10x15 mm", "H 400x400x13x21 mm"
    ], index=2)
    
    # ตั้งค่าตั้งต้นตามพรีเซ็ต
    d_init, bf_init, tw_init, tf_init = 300.0, 300.0, 10.0, 15.0
    if "200x200" in thai_steel_preset: d_init, bf_init, tw_init, tf_init = 200.0, 200.0, 8.0, 12.0
    elif "250x250" in thai_steel_preset: d_init, bf_init, tw_init, tf_init = 250.0, 250.0, 9.0, 14.0
    elif "400x400" in thai_steel_preset: d_init, bf_init, tw_init, tf_init = 400.0, 400.0, 13.0, 21.0

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1: col_d_mm = st.number_input("ลึกเสา d (mm)", min_value=100.0, value=d_init)
    with c_m2: col_bf_mm = st.number_input("กว้างปีก bf (mm)", min_value=100.0, value=bf_init)
    with c_m3: col_tw_mm = st.number_input("หนาเอว tw (mm)", min_value=4.0, value=tw_init)
    with c_m4: col_tf_mm = st.number_input("หนาปีก tf (mm)", min_value=4.0, value=tf_init)

    # แปลงหน่วยมิลลิเมตรเข้าสู่ระบบคำนวณนิ้ว (AISC Mechanics Engine Backend)
    d_in, bf_in, tw_in, tf_in = col_d_mm/25.4, col_bf_mm/25.4, col_tw_mm/25.4, col_tf_mm/25.4

    st.markdown("**ป้อนค่าน้ำหนักบรรทุกประลัย (Factored Loads):**")
    cx1, cx2, cx3 = st.columns(3)
    with cx1: p_u = st.number_input("แรงกด Pu (kips)", min_value=1.0, value=150.0)
    with cx2: v_u = st.number_input("แรงเฉือน Vu (kips)", min_value=0.0, value=30.0)
    with cx3: m_u = st.number_input("โมเมนต์ดัด Mu (kip-in)", min_value=0.0, value=600.0)
    
    fc_prime = st.number_input("กำลังอัดคอนกรีตฐานราก fc' (ksi)", min_value=2.0, value=4.0)

    # -------------------------------------------------
    # STEP 2: METRIC BASE PLATE CONFIGURATION
    # -------------------------------------------------
    st.markdown("<div class='step-header'>📐 STEP 2: ออกแบบมิติแผ่นฐานและสุ่มตรวจความหนาแผ่นเหล็ก มอก.</div>", unsafe_allow_html=True)
    
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_prime
    rec_B_in = bf_in + 4.0
    rec_N_in = d_in + 4.0
    
    st.info(f"💡 **ระยะครอบคลุมหน้าตัดแสตมป์ขั้นต่ำ:** แนะนำให้ใช้แผ่นฐานขนาดอย่างน้อย {round(rec_B_in, 1)} x {round(rec_N_in, 1)} นิ้ว เพื่อให้มีพื้นที่เหลือเชื่อมแนวรอบขาเสาได้สมบูรณ์")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1: B = st.number_input("ระบุความกว้างแผ่นฐานจริง B (นิ้ว)", min_value=float(bf_in), value=float(math.ceil(rec_B_in)))
    with c_p2: N = st.number_input("ระบุความยาวแผ่นฐานจริง N (นิ้ว)", min_value=float(d_in), value=float(math.ceil(rec_N_in)))

    # การวิเคราะห์พฤติกรรมเยื้องศูนย์ขั้นสูง (Rigorous Mechanics)
    ecc = m_u / p_u if p_u > 0 else 0.0
    kern = N / 6.0
    edge_g = 2.5 # ระยะร่นเจาะรูโบลต์มาตรฐานจากขอบเพลต
    f_dist = (N / 2.0) - edge_g
    
    Y_length, t_req_min, bearing_stress_actual, tension_total = 0.0, 0.0, 0.0, 0.0

    if ecc <= kern:
        bearing_stress_actual = (p_u / (B * N)) * (1.0 + (6.0 * ecc / N))
        Y_length = N
        m = (N - 0.95 * d_in) / 2.0
        n = (B - 0.80 * bf_in) / 2.0
        t_req_min = max(m, n) * math.sqrt((2.0 * p_u) / (0.90 * 36.0 * B * N))
    else:
        # พฤติกรรมแรงดัดสูงมาก (Large Overturning Moment) นอตโดนงัดดึง
        a_coeff = B * f_p_max / 2.0
        b_coeff = -B * f_p_max * (f_dist + N/2.0)
        c_coeff = p_u * (ecc + f_dist)
        discriminant = b_coeff**2 - 4.0 * a_coeff * c_coeff
        if discriminant >= 0:
            Y_length = (-b_coeff - math.sqrt(discriminant)) / (2.0 * a_coeff)
            bearing_stress_actual = f_p_max
            tension_total = (f_p_max * B * Y_length / 2.0) - p_u
        else:
            Y_length = N
            bearing_stress_actual = f_p_max
            tension_total = 0.0
            
        m = (N - 0.95 * d_in) / 2.0
        if Y_length >= m:
            t_req_min = m * math.sqrt((2.0 * bearing_stress_actual) / (0.90 * 36.0))
        else:
            t_req_min = math.sqrt((4.0 * tension_total * (f_dist - d_in/2.0)) / (0.90 * 36.0 * B))

    selected_thickness_label = st.selectbox("เลือกความหนาแผ่นเหล็กตามสเปกตลาดไทย (mm):", list(THAI_PLATE_THICKNESSES.keys()), index=2)
    tp_in = THAI_PLATE_THICKNESSES[selected_thickness_label] / 25.4

    # -------------------------------------------------
    # STEP 3: DISCRETE FLANGE & WEB WELD SEPARATION
    # -------------------------------------------------
    st.markdown("<div class='step-header'>⚡ STEP 3: ออกแบบแยกส่วนแนวเชื่อมขาเสา (Flange vs. Web Welding)</div>", unsafe_allow_html=True)
    
    # คำนวณความยาวแนวเชื่อมแบ่งตามสัดส่วนพื้นที่หน้าตัดจริง
    length_weld_flange = 4.0 * bf_in  # เชื่อมรอบปีกนอกและปีกในเสา
    length_weld_web = 2.0 * (d_in - (2.0 * tf_in)) # เชื่อมเอวเสาสองฝั่ง
    
    base_weld_size = st.slider("เลือกขนาดขารอยเชื่อมจริง (หน่วย หุน หรือ ส่วน 1/16 นิ้ว):", min_value=2, max_value=10, value=4)
    weld_leg = base_weld_size / 16.0
    weld_capacity_per_inch = 0.75 * 0.60 * 70.0 * 0.707 * weld_leg

    # การถ่ายแรง: โมเมนต์ดัด Mu และแรงกด Pu ส่วนใหญ่จะเข้าสู่รอยเชื่อมปีกเสา (Flange Welds)
    # ขณะที่แรงเฉือน Vu ทั้งหมดจะวิ่งไหลเข้าสู่รอยเชื่อมเอวเสา (Web Welds)
    weld_demand_flange = (p_u / (length_weld_flange + length_weld_web)) + (m_u / (bf_in * (d_in - tf_in)))
    weld_demand_web = v_u / length_weld_web if length_weld_web > 0 else 0.0

    st.markdown(f"""
    * 🔹 **ที่บริเวณปีกเสา (Flange):** รับแรงกดรวมแรงดัดรวมกันสูงถึง <span class='weld-label'>{round(weld_demand_flange, 2)} kips/นิ้ว</span> (กำลังต้านทานรอยเชื่อมที่มี: {round(weld_capacity_per_inch, 2)} kips/นิ้ว)
    * 🔹 **ที่บริเวณเอวเสา (Web):** รับเฉพาะแรงเฉือนตรงพังทลายสไลด์ขาเสา <span class='weld-label'>{round(weld_demand_web, 2)} kips/นิ้ว</span>
    """, unsafe_allow_html=True)

    # -------------------------------------------------
    # STEP 4: BOLT MAP & STATE ASSIGNMENT
    # -------------------------------------------------
    st.markdown("<div class='step-header'>🔩 STEP 4: แผนผังจำแนกสถานะกลุ่มโบลต์รับแรงดึงดัด (Anchor Bolt Mapping)</div>", unsafe_allow_html=True)
    
    num_anchors = st.selectbox("กำหนดจำนวนสลักเกลียวฝังทั้งหมดที่หน้างาน:", [4, 6, 8], index=0)
    selected_bolt = st.selectbox("เลือกขนาดแกนโบลต์มาตรฐานอุตสาหกรรมไทย:", list(THAI_ANCHOR_BOLTS.keys()), index=2)
    bolt_profile = THAI_ANCHOR_BOLTS[selected_bolt]
    
    # คำนวณพฤติกรรมแยกข้างรายตัว
    bolts_in_tension_zone = num_anchors / 2
    tension_per_bolt = tension_total / bolts_in_tension_zone if tension_total > 0 else 0.0
    shear_per_bolt = v_u / num_anchors
    
    phi_b = 0.75
    cap_tension_single = phi_b * bolt_profile["F_nt"] * bolt_profile["area_in2"]
    cap_shear_single = phi_b * bolt_profile["F_nv"] * bolt_profile["area_in2"]

    st.markdown(f"""
    * 🟥 **กลุ่มโบลต์ฝั่งรับโมเมนต์งัด (Tension Side จำนวน {int(bolts_in_tension_zone)} ตัว):** ต้องแบกรับแรงดึงสุทธิถึงตัวละ <span class='bolt-tension'>{round(tension_per_bolt, 2)} kips</span>
    * 🟩 **กลุ่มโบลต์ฝั่งจมแรงอัด (Compression/Clamping Side จำนวน {int(bolts_in_tension_zone)} ตัว):** ไม่เกิดแรงดึงตัวนอตทำหน้าที่แค่ยึดตรึงพิกัดตำแหน่ง (Tension = <span class='bolt-compression'>0.00 kips</span>)
    """, unsafe_allow_html=True)

# ================= ================= =================
# 4. PROFESSIONAL ENGINEERING DASHBOARD (RIGHT COLUMN)
# ================= ================= =================
with ui_right:
    st.markdown("### 📊 AISC Structural Verification Matrix")
    st.caption("ตารางตรวจสอบขีดความสามารถประลัยแยกจุดวิกฤต (Component Limit States)")

    # สรุปเปอร์เซ็นต์การแบกรับแรงเค้นสูงสุด (Utilization Ratio Matrix)
    util_bearing = (bearing_stress_actual / f_p_max) * 100
    util_plate = (t_req_min / tp_in) * 100
    util_weld_flange = (weld_demand_flange / weld_capacity_per_inch) * 100
    util_weld_web = (weld_demand_web / weld_capacity_per_inch) * 100
    util_bolt_t = (tension_per_bolt / cap_tension_single) * 100 if cap_tension_single > 0 else 0
    util_bolt_v = (shear_per_bolt / cap_shear_single) * 100

    report_data = [
        {"Component Limit State Check": "1. คอนกรีตรับแรงกดตอม่อ (Concrete Bearing)", "Demand": f"{round(bearing_stress_actual, 2)} ksi", "Capacity (φRn)": f"{round(f_p_max, 2)} ksi", "Ratio %": f"{round(util_bearing, 1)}%", "Status": "PASS" if util_bearing<=100 else "FAIL"},
        {"Component Limit State Check": "2. ความหนาแผ่นเหล็กเพลตฐาน (Plate Bending)", "Demand": f"{round(t_req_min, 3)} in", "Capacity (φRn)": f"{round(tp_in, 3)} in", "Ratio %": f"{round(util_plate, 1)}%", "Status": "PASS" if util_plate<=100 else "FAIL"},
        {"Component Limit State Check": "3. รอยเชื่อมบริเวณปีกเสาเหล็ก (Flange Weld)", "Demand": f"{round(weld_demand_flange, 2)} k/in", "Capacity (φRn)": f"{round(weld_capacity_per_inch, 2)} k/in", "Ratio %": f"{round(util_weld_flange, 1)}%", "Status": "PASS" if util_weld_flange<=100 else "FAIL"},
        {"Component Limit State Check": "4. รอยเชื่อมบริเวณเอวเสาเหล็ก (Web Weld)", "Demand": f"{round(weld_demand_web, 2)} k/in", "Capacity (φRn)": f"{round(weld_capacity_per_inch, 2)} k/in", "Ratio %": f"{round(util_weld_web, 1)}%", "Status": "PASS" if util_weld_web<=100 else "FAIL"},
        {"Component Limit State Check": "5. ตัวโบลต์ฝั่งรับแรงดึงงัด (Bolt Tension-only)", "Demand": f"{round(tension_per_bolt, 2)} kips", "Capacity (φRn)": f"{round(cap_tension_single, 2)} kips", "Ratio %": f"{round(util_bolt_t, 1)}%", "Status": "PASS" if util_bolt_t<=100 else "FAIL"},
        {"Component Limit State Check": "6. ตัวโบลต์รับแรงเฉือนสไลด์ (Bolt Shear-only)", "Demand": f"{round(shear_per_bolt, 2)} kips", "Capacity (φRn)": f"{round(cap_shear_single, 2)} kips", "Ratio %": f"{round(util_bolt_v, 1)}%", "Status": "PASS" if util_bolt_v<=100 else "FAIL"},
    ]
    st.table(report_data)

    max_util = max([util_bearing, util_plate, util_weld_flange, util_weld_web, util_bolt_t, util_bolt_v])
    if max_util > 100:
        st.error(f"❌ OVERSTRESSED CRITICAL ({round(max_util, 1)}%): โครงสร้างจุดต่อบางชิ้นส่วนเกินขีดจำกัดความปลอดภัยขั้นรุนแรง!")
    else:
        st.success(f"✅ STRUCTURAL SAFE ({round(max_util, 1)}%): ชิ้นส่วนจุดต่อทั้งหมดผ่านเกณฑ์ควบคุมมาตรฐาน LRFD และใช้งานได้จริงหน้างาน")

    st.markdown("---")
    st.markdown("### 🧊 High-Fidelity 3D Mechanical Spatial Model")
    st.caption("โมเดลแสดงสัดส่วนจริงของหน้าตัดเสา H-Beam, การจัดวางรอยเชื่อมแยกสี (ปีก-น้ำเงิน / เอว-ฟ้า), บล็อกลิ่มแรงกดสีส้ม และลูกศรสีแดงแสดงเวกเตอร์แรงดึงพุ่งจากหัวโบลต์ที่มีแรงงัดจริง")
    
    # รันโมเดล 3 มิติความละเอียดสูง
    fig_hf_model = generate_high_fidelity_3d(B, N, tp_in, d_in, bf_in, tw_in, tf_in, num_anchors, Y_length, tension_per_bolt, edge_g)
    st.plotly_chart(fig_hf_model, use_container_width=True)
