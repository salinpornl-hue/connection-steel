# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. METRIC DATABASE & MATERIALS (THAI STANDARDS)
# ================= ================= =================
THAI_PLATE_THICKNESSES_MM = {
    "12 mm": 12.0, "16 mm": 16.0, "19 mm": 19.0, "22 mm": 22.0, 
    "25 mm": 25.0, "28 mm": 28.0, "32 mm": 32.0, "38 mm": 38.0, "50 mm": 50.0
}

# สลักเกลียวตามมาตรฐาน มอก. / ISO (Grade 4.6 และ 8.8 ยอดนิยม)
THAI_ANCHOR_BOLTS_MM = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area_as": 157.0, "F_nt": 300.0, "F_nv": 180.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area_as": 245.0, "F_nt": 300.0, "F_nv": 180.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area_as": 353.0, "F_nt": 300.0, "F_nv": 180.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area_as": 561.0, "F_nt": 600.0, "F_nv": 360.0},
    "M36 (Grade 8.8)": {"dia": 36.0, "area_as": 817.0, "F_nt": 600.0, "F_nv": 360.0}
}

st.set_page_config(page_title="AISC-Thai Metric Connection Engine", layout="wide")
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .weld-label { font-weight: bold; color: #0275d8; }
    .bolt-tension { color: #d9534f; font-weight: bold; }
    .bolt-compression { color: #5cb85c; font-weight: bold; }
    .step-header { background-color: #1a365d; color: white; padding: 8px 15px; border-radius: 4px; margin-top: 15px; margin-bottom: 10px; font-weight: bold; }
    .error-box { background-color: #ffebee; color: #c62828; padding: 12px; border-radius: 4px; border-left: 6px solid #e53935; margin-bottom: 10px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ AISC-Thai Metric High-Fidelity Connection Engine")
st.caption("ระบบวิเคราะห์จุดต่อแผ่นฐานเสาเหล็กและกลศาสตร์รอยเชื่อม-โบลต์รายตัว หน่วยเมตริก (mm, kN, MPa) | AISC 360 LRFD Metric Equivalent")

# ================= ================= =================
# 2. METRIC 3D VISUALIZATION WITH GLOBAL LOAD VECTORS
# ================= ================= =================
def generate_metric_3d(B, N, tp, d, bf, tw, tf, num_anchors, Y_length, tension_per_bolt, edge_g, P_u, V_u, M_u):
    fig = go.Figure()
    h_col = 500.0 # ความสูงเสาจำลองหน่วย mm

    # 1. คอนกรีตตอม่อโปร่งแสง (Concrete Pedestal Volume)
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-400, -400, -400, -400, 0, 0, 0, 0],
        color='lightgrey', opacity=0.15, name='Concrete Pedestal', showlegend=True
    ))

    # 2. แผ่นฐานเหล็กหนาจริง (Solid Base Plate)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='rgb(100, 110, 120)', opacity=0.85, name='Base Plate'
    ))

    # 3. หน้าตัดเสาเหล็ก H-Beam แบบ Solid Volumes แยกชิ้นส่วนปีกและเอวเสาชัดเจน
    # ปีกเสาฝั่งซ้าย (-Y)
    fig.add_trace(go.Mesh3d(
        x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2],
        y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(55, 65, 80)', opacity=0.95, name='Column Flanges'
    ))
    # ปีกเสาฝั่งขวา (+Y)
    fig.add_trace(go.Mesh3d(
        x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2],
        y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(55, 65, 80)', opacity=0.95, showlegend=False
    ))
    # เอวเสาตรงกลาง (Web)
    fig.add_trace(go.Mesh3d(
        x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2],
        y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf],
        z=[tp, tp, tp, tp, tp+h_col, tp+h_col, tp+h_col, tp+h_col],
        color='rgb(75, 85, 100)', opacity=0.95, name='Column Web'
    ))

    # 4. แสดงแนวรอยเชื่อมรอบหน้าตัด (Weld Lines Visualization)
    # รอยเชื่อมปีกนอกเสา (Flange Welds - สีน้ำเงินเข้ม)
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+1, tp+1], mode='lines', line=dict(color='blue', width=6), name='Flange Weld'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+1, tp+1], mode='lines', line=dict(color='blue', width=6), showlegend=False))
    # รอยเชื่อมเอวเสา (Web Welds - สีฟ้าคราม)
    fig.add_trace(go.Scatter3d(x=[-tw/2-1, -tw/2-1], y=[-d/2+tf, d/2-tf], z=[tp+1, tp+1], mode='lines', line=dict(color='cyan', width=5), name='Web Weld'))
    fig.add_trace(go.Scatter3d(x=[tw/2+1, tw/2+1], y=[-d/2+tf, d/2-tf], z=[tp+1, tp+1], mode='lines', line=dict(color='cyan', width=5), showlegend=False))

    # 5. พิกัดสลักเกลียวฝังแบบจำแนกสถานะแรงดึง (Anchor Bolt Map)
    ex, ey = (B/2) - edge_g, (N/2) - edge_g
    if num_anchors == 4: coords = [(-ex, -ey), (ex, -ey), (-ex, ey), (ex, ey)]
    elif num_anchors == 6: coords = [(-ex, -ey), (ex, -ey), (-ex, 0), (ex, 0), (-ex, ey), (ex, ey)]
    else: coords = [(-ex, -ey), (ex, -ey), (-ex, 0), (ex, 0), (-ex, ey), (ex, ey), (0, -ey), (0, ey)]

    for idx, (bx, by) in enumerate(coords):
        is_tension_side = True if by > 0 else False
        bolt_color = 'rgb(230, 40, 40)' if (is_tension_side and tension_per_bolt > 0) else 'rgb(40, 190, 70)'
        bolt_name = 'Anchor (Tension)' if (is_tension_side and tension_per_bolt > 0) else 'Anchor (Clamping/Comp.)'
        
        # ก้านโบลต์ฝังลึก
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-300, tp+40], mode='lines+markers',
            marker=dict(size=4, color=bolt_color), line=dict(color=bolt_color, width=6),
            name=bolt_name, showlegend=True if idx in [0, 2] else False
        ))
        
        # ลูกศรเวกเตอร์แรงดึงรายตัว (Individual Bolt Tension Arrow)
        if is_tension_side and tension_per_bolt > 0:
            fig.add_trace(go.Cone(
                x=[bx], y=[by], z=[tp+40], u=[0], v=[0], w=[tension_per_bolt*1.5 + 40],
                sizemode="absolute", sizeref=40, showscale=False, colorscale=[[0,'red'],[1,'red']], name='Bolt Tension Vector'
            ))

    # 6. ลิ่มแรงกดคอนกรีตสีส้ม (Concrete Bearing Contact Zone)
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2],
            z=[0, 0, 0, 0, -50, -50, -50, -50],
            color='rgba(255, 130, 0, 0.5)', name='Concrete Bearing Block'
        ))

    # 7. 🔥 เพิ่มเวกเตอร์แรงประลัยหลักหลัก (GLOBAL LOAD ARROWS) ที่หัวเสา
    # แรงกดเครื่องหมายลบพุ่งลง (Axial Compression Vector)
    fig.add_trace(go.Cone(
        x=[0], y=[0], z=[tp+h_col+120], u=[0], v=[0], w=[-100],
        sizemode="absolute", sizeref=50, showscale=False, colorscale=[[0,'black'],[1,'black']], name='Pu (Compression Force)'
    ))
    # แรงเฉือนพุ่งตามแกน Y (Shear Force Vector)
    if V_u > 0:
        fig.add_trace(go.Cone(
            x=[0], y=[-100], z=[tp+h_col], u=[0], v=[100], w=[0],
            sizemode="absolute", sizeref=40, showscale=False, colorscale=[[0,'purple'],[1,'purple']], name='Vu (Shear Force)'
        ))
    # โมเมนต์ดัดแสดงด้วยแรงคู่ควบคู่ดึง-กดที่หัวเสา (Moment Couple Representation)
    if M_u > 0:
        # ฝั่งซ้ายกดลง
        fig.add_trace(go.Cone(x=[0], y=[-d/2], z=[tp+h_col+60], u=[0], v=[0], w=[-60], sizemode="absolute", sizeref=30, showscale=False, colorscale=[[0,'orange'],[1,'orange']], name='Mu Couple (Compression)'))
        # ฝั่งขวางัดขึ้น
        fig.add_trace(go.Cone(x=[0], y=[d/2], z=[tp+h_col], u=[0], v=[0], w=[60], sizemode="absolute", sizeref=30, showscale=False, colorscale=[[0,'magenta'],[1,'magenta']], name='Mu Couple (Tension)'))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='X (Width) [mm]'), yaxis=dict(title='Y (Length) [mm]'), zaxis=dict(title='Z (Height) [mm]'),
            aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.0))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=620
    )
    return fig

# ================= ================= =================
# 3. INTERACTIVE METRIC MECHANICAL DESIGN CONTROLS
# ================= ================= =================
col_ctrl, col_view = st.columns([1.1, 0.9])

with col_ctrl:
    st.markdown("<div class='step-header'>📍 STEP 1: มิติหน้าตัดเสาเหล็ก H-Beam แท้ (มิลลิเมตร)</div>", unsafe_allow_html=True)
    
    thai_steel_preset = st.selectbox("เลือกหน้าตัดเสา H-Beam สำเร็จรูป (มอก. 1227-2558):", [
        "Custom (ระบุค่าเอง)", "H 200x200x8x12 mm", "H 250x250x9x14 mm", "H 300x300x10x15 mm", "H 400x400x13x21 mm"
    ], index=3)
    
    # ค่าเริ่มต้น (Default สำหรับหน้าตัด H 300x300 หรือผันตามพรีเซ็ต)
    d, bf, tw, tf = 300.0, 300.0, 10.0, 15.0
    if "200x200" in thai_steel_preset: d, bf, tw, tf = 200.0, 200.0, 8.0, 12.0
    elif "250x250" in thai_steel_preset: d, bf, tw, tf = 250.0, 250.0, 9.0, 14.0
    elif "400x400" in thai_steel_preset: d, bf, tw, tf = 400.0, 400.0, 13.0, 21.0

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1: d = st.number_input("ความลึกรวม d (mm)", min_value=50.0, value=d)
    with c_m2: bf = st.number_input("กว้างปีกเสา bf (mm)", min_value=50.0, value=bf)
    with c_m3: tw = st.number_input("หนาเอวเสา tw (mm)", min_value=2.0, value=tw)
    with c_m4: tf = st.number_input("หนาปีกเสา tf (mm)", min_value=2.0, value=tf)

    st.markdown("**ระบุน้ำหนักบรรทุกประลัยหน่วงงาน (Factored Metric Loads):**")
    cx1, cx2, cx3 = st.columns(3)
    with cx1: p_u_kn = st.number_input("แรงกดแนวแกน Pu (kN)", min_value=1.0, value=650.0)
    with cx2: v_u_kn = st.number_input("แรงเฉือนฐาน Vu (kN)", min_value=0.0, value=120.0)
    with cx3: m_u_knm = st.number_input("โมเมนต์ดัดพลิก Mu (kN-m)", min_value=0.0, value=90.0)
    
    fc_mpa = st.number_input("กำลังอัดคอนกรีตฐานราก fc' (MPa)", min_value=15.0, value=28.0)

    st.markdown("<div class='step-header'>📐 STEP 2: ขนาดแผ่นฐานเหล็กเพลต และเช็กระยะขัดแย้ง (Geometry Matching)</div>", unsafe_allow_html=True)
    
    rec_B = bf + 100.0
    rec_N = d + 100.0
    st.info(f"💡 **สัดส่วนแนะนำสำหรับระนาบเชื่อมรอบเสา:** เพลตควรมีขนาดอย่างน้อย {int(rec_B)} x {int(rec_N)} mm")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1: B = st.number_input("ความกว้างแผ่นฐานจริง B (mm)", min_value=bf+20.0, value=float(math.ceil(rec_B/10)*10))
    with c_p2: N = st.number_input("ความยาวแผ่นฐานจริง N (mm)", min_value=d+20.0, value=float(math.ceil(rec_N/10)*10))

    edge_g = st.number_input("ระยะร่นเจาะรูสลักเกลียวจากขอบเพลตเดี่ยว edge distance (mm)", min_value=25.0, value=60.0)

    # 🛑 ตรวจสอบความสอดคล้องทางเรขาคณิต (Geometric Compatibility Check) ตามที่คุณสั่ง!
    bolt_y_position = (N / 2.0) - edge_g  # ระยะพิกัดโบลต์จากจุดศูนย์กลาง
    flange_outer_edge = d / 2.0           # ระยะขอบนอกของปีกเสา
    bolt_clearance = bolt_y_position - flange_outer_edge

    if bolt_clearance < 45.0:
        st.markdown(f"""
        <div class='error-box'>
        ⚠️ ระยะติดตั้งโบลต์ไม่สอดคล้องกับขนาดเหล็กโครงสร้าง!<br>
        ระยะห่างจากแกนโบลต์ถึงขอบปีกเสาเหลือเพียง {round(bolt_clearance,1)} mm ซึ่งน้อยกว่าเกณฑ์ช่างขั้นต่ำ (45 mm)<br>
        <b>ผลกระทบ:</b> หัวโบลต์จะชนปีกเสา ขันรอยเชื่อมหรือประแจปอนด์ไม่ได้! กรุณาเพิ่มความยาวแผ่นฐาน N หรือลดระยะร่นขอบเพลต
        </div>
        """, unsafe_allow_html=True)

    # คำนวณขีดจำกัดแรงกดคอนกรีต (AISC LRFD Metric Section)
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa  # กำลังกดประลัยของหน้าคอนกรีตสัมผัส (MPa)
    
    # แปลงหน่วยเข้าสูตรกลศาสตร์หลักเพื่อหาจุดสะเทินและแรงดึงโบลต์
    P_u_n = p_u_kn * 1000.0
    V_u_n = v_u_kn * 1000.0
    M_u_nmm = m_u_knm * 1000000.0
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    
    f_dist = (N / 2.0) - edge_g # ระยะจากจุดศูนย์กลางเพลตไปยังแนวแกนโบลต์ฝั่งรับแรงดึง
    Y_length, t_req_min, bearing_stress_actual, tension_total = 0.0, 0.0, 0.0, 0.0

    if ecc <= (N / 6.0):
        # แผ่นฐานรับแรงอัดเต็มพื้นที่ ไม่มีแรงดึงในสลักเกลียว
        bearing_stress_actual = (P_u_n / (B * N)) * (1.0 + (6.0 * ecc / N))
        Y_length = N
        m = (N - 0.95 * d) / 2.0
        n = (B - 0.80 * bf) / 2.0
        t_req_min = max(m, n) * math.sqrt((2.0 * P_u_n) / (0.90 * 245.0 * B * N))
    else:
        # มีแรงดัดพลิกคว่ำสูง เกิดลิ่มแรงกดบางส่วนและโบลต์ถูกงัดขึ้นงอพัง
        a_coeff = B * f_p_max / 2.0
        b_coeff = -B * f_p_max * (f_dist + N/2.0)
        c_coeff = P_u_n * (ecc + f_dist)
        discriminant = b_coeff**2 - 4.0 * a_coeff * c_coeff
        if discriminant >= 0:
            Y_length = (-b_coeff - math.sqrt(discriminant)) / (2.0 * a_coeff)
            bearing_stress_actual = f_p_max
            tension_total = (f_p_max * B * Y_length / 2.0) - P_u_n
        else:
            Y_length = N
            bearing_stress_actual = f_p_max
            tension_total = 0.0
            
        m = (N - 0.95 * d) / 2.0
        if Y_length >= m:
            t_req_min = m * math.sqrt((2.0 * bearing_stress_actual) / (0.90 * 245.0))
        else:
            t_req_min = math.sqrt((4.0 * tension_total * (f_dist - d/2.0)) / (0.90 * 245.0 * B))

    selected_thickness_label = st.selectbox("เลือกความหนาเหล็กแผ่นฐานที่มีขายในไทยจริง (mm):", list(THAI_PLATE_THICKNESSES_MM.keys()), index=3)
    tp = THAI_PLATE_THICKNESSES_MM[selected_thickness_label]

    st.markdown("<div class='step-header'>⚡ STEP 3: ตรวจสอบความเพียงพอของรอยเชื่อมแยก ปีก vs. เอว (Weld Sufficiency)</div>", unsafe_allow_html=True)
    
    # คำนวณความยาวแนวเชื่อมประสานเนื้อเหล็กจริง
    length_weld_flange = 4.0 * bf  
    length_weld_web = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0
    
    weld_size_mm = st.slider("เลือกขนาดขาของรอยเชื่อมพอกจริงด้านหน้างาน aw (mm):", min_value=3, max_value=16, value=6)
    
    # กำลังรอยเชื่อมประลัยต่อหน่วยมิลลิเมตรตามมาตรฐานลวดเชื่อม E70XX (Fu = 490 MPa)
    weld_capacity_per_mm = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0 # คืนค่าเป็น kN/mm

    # การกระจายแรงตามพฤติกรรมจริง: ปีกรับโมเมนต์และแรงกดตรง, เอวเสารับแรงเฉือนแนวราบ
    weld_demand_flange = ((P_u_n / (length_weld_flange + length_weld_web)) + (M_u_nmm / (bf * (d - tf)))) / 1000.0 # kN/mm
    weld_demand_web = (V_u_n / length_weld_web) / 1000.0 if length_weld_web > 0 else 0.0 # kN/mm

    st.markdown(f"""
    * 🔹 **รอยเชื่อมที่ปีกเสา (Flange):** แรงเค้นแผ่จริง <span class='weld-label'>{round(weld_demand_flange, 3)} kN/mm</span> (กำลังต้านทานรอยเชื่อมที่มี: {round(weld_capacity_per_mm, 3)} kN/mm)
    * 🔹 **รอยเชื่อมที่เอวเสา (Web):** แรงเค้นแรงเฉือนจริง <span class='weld-label'>{round(weld_demand_web, 3)} kN/mm</span>
    """, unsafe_allow_html=True)

    st.markdown("<div class='step-header'>🔩 STEP 4: การจัดกลุ่มโบลต์และเช็กความพังทลายสลักเกลียวรายตัว</div>", unsafe_allow_html=True)
    
    num_anchors = st.selectbox("เลือกจำนวนสลักเกลียวฝัง (ตัว):", [4, 6, 8], index=0)
    selected_bolt = st.selectbox("เลือกขนาดระบุแกนโบลต์อุตสาหกรรมไทย (มิลลิเมตร):", list(THAI_ANCHOR_BOLTS_MM.keys()), index=2)
    bolt_profile = THAI_ANCHOR_BOLTS_MM[selected_bolt]
    
    bolts_in_tension_zone = num_anchors / 2
    tension_per_bolt_kn = (tension_total / 1000.0) / bolts_in_tension_zone if tension_total > 0 else 0.0
    shear_per_bolt_kn = v_u_kn / num_anchors
    
    phi_b = 0.75
    cap_tension_single_kn = (phi_b * bolt_profile["F_nt"] * bolt_profile["area_as"]) / 1000.0
    cap_shear_single_kn = (phi_b * bolt_profile["F_nv"] * bolt_profile["area_as"]) / 1000.0

    st.markdown(f"""
    * 🟥 **กลุ่มโบลต์ฝั่งรับโมเมนต์งัดพลิก (Tension Side จำนวน {int(bolts_in_tension_zone)} ตัว):** ต้องแบกรับแรงดึงดัดสุทธิตัวละ <span class='bolt-tension'>{round(tension_per_bolt_kn, 1)} kN</span>
    * 🟩 **กลุ่มโบลต์ฝั่งรับแรงอัดคอนกรีต (Compression Side จำนวน {int(bolts_in_tension_zone)} ตัว):** แรงดึงเป็นศูนย์ (<span class='bolt-compression'>0.0 kN</span>) ทำหน้าที่เป็นหมุดยึดตำแหน่งชั่วคราว
    """, unsafe_allow_html=True)

# ================= ================= =================
# 4. METRIC ENGINEERING REPORT & HIGH-FIDELITY VIEW
# ================= ================= =================
with col_view:
    st.markdown("### 📊 AISC Metric Verification Matrix")
    st.caption("ตารางประเมินขีดความสามารถประลัยชิ้นส่วนแยกสถานะจำกัดความปลอดภัย (Limit States)")

    # อัตราการรับแรงเค้นสูงสุดจำแนกจุด (%)
    util_bearing = (bearing_stress_actual / f_p_max) * 100 if f_p_max > 0 else 0
    util_plate = (t_req_min / tp) * 100 if tp > 0 else 0
    util_weld_flange = (weld_demand_flange / weld_capacity_per_mm) * 100 if weld_capacity_per_mm > 0 else 0
    util_weld_web = (weld_demand_web / weld_capacity_per_mm) * 100 if weld_capacity_per_mm > 0 else 0
    util_bolt_t = (tension_per_bolt_kn / cap_tension_single_kn) * 100 if cap_tension_single_kn > 0 else 0
    util_bolt_v = (shear_per_bolt_kn / cap_shear_single_kn) * 100 if cap_shear_single_kn > 0 else 0

    report_data = [
        {"หน่วยตรวจสอบวิศวกรรม": "1. คอนกรีตรับแรงอัดใต้ฐานเพลต (Concrete Bearing)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(bearing_stress_actual, 1)} MPa", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(f_p_max, 1)} MPa", "สัดส่วนแรงเค้น %": f"{round(util_bearing, 1)}%", "สถานะ": "PASS" if util_bearing<=100 else "FAIL"},
        {"หน่วยตรวจสอบวิศวกรรม": "2. ความหนาเหล็กแผ่นฐานเพลต (Plate Thickness)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(t_req_min, 1)} mm", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(tp, 1)} mm", "สัดส่วนแรงเค้น %": f"{round(util_plate, 1)}%", "สถานะ": "PASS" if util_plate<=100 else "FAIL"},
        {"หน่วยตรวจสอบวิศวกรรม": "3. เนื้อรอยเชื่อมรอบปีกเสาเหล็ก (Flange Weld)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(weld_demand_flange, 3)} kN/mm", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(weld_capacity_per_mm, 3)} kN/mm", "สัดส่วนแรงเค้น %": f"{round(util_weld_flange, 1)}%", "สถานะ": "PASS" if util_weld_flange<=100 else "FAIL"},
        {"หน่วยตรวจสอบวิศวกรรม": "4. เนื้อรอยเชื่อมรอบเอวเสาเหล็ก (Web Weld)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(weld_demand_web, 3)} kN/mm", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(weld_capacity_per_mm, 3)} kN/mm", "สัดส่วนแรงเค้น %": f"{round(util_weld_web, 1)}%", "สถานะ": "PASS" if util_weld_web<=100 else "FAIL"},
        {"หน่วยตรวจสอบวิศวกรรม": "5. โบลต์ฝั่งรับโมเมนต์งัดขึ้น (Bolt Tension)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(tension_per_bolt_kn, 1)} kN", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(cap_tension_single_kn, 1)} kN", "สัดส่วนแรงเค้น %": f"{round(util_bolt_t, 1)}%", "สถานะ": "PASS" if util_bolt_t<=100 else "FAIL"},
        {"หน่วยตรวจสอบวิศวกรรม": "6. โบลต์รับแรงเฉือนสไลด์ฐาน (Bolt Shear)", "ค่าแรงที่เกิดขึ้นจริง": f"{round(shear_per_bolt_kn, 1)} kN", "ขีดความสามารถสูงสุดที่ยอมรับได้": f"{round(cap_shear_single_kn, 1)} kN", "สัดส่วนแรงเค้น %": f"{round(util_bolt_v, 1)}%", "สถานะ": "PASS" if util_bolt_v<=100 else "FAIL"},
    ]
    st.table(report_data)

    max_util = max([util_bearing, util_plate, util_weld_flange, util_weld_web, util_bolt_t, util_bolt_v])
    if max_util > 100:
        st.error(f"❌ โครงสร้างไม่ปลอดภัยคริติคอล ({round(max_util, 1)}%): มีบางชิ้นส่วนรับแรงเค้นเกินขีดจำกัดความปลอดภัยขั้นรุนแรง!")
    elif bolt_clearance < 45.0:
        st.warning(f"⚠️ โครงสร้างผ่านเกณฑ์ต้านทานแรง ({round(max_util, 1)}%) แต่ไม่ผ่านเกณฑ์ติดตั้งเชิงเรขาคณิต (ระยะห่างโบลต์-เสา ชนกันหน้างาน)")
    else:
        st.success(f"✅ จุดต่อปลอดภัยสมบูรณ์และติดตั้งได้จริง ({round(max_util, 1)}%): ทุกจุดผ่านเกณฑ์ทางกลศาสตร์ LRFD และสอดคล้องกับหน้างานจริง")

    st.markdown("---")
    st.markdown("### 🧊 High-Fidelity 3D Engineering Spatial Model (Metric)")
    st.caption("ระบบแสดงมิติจริงของเสา H-Beam แยกชิ้น, แนวรอยเชื่อมปีก (สีน้ำเงิน) / เอว (สีฟ้า), ลิ่มคอนกรีตสัมผัส (สีส้ม), เวกเตอร์แรงกดหัวเสา Pu (ลูกศรสีดำ), แรงเฉือน Vu (ลูกศรสีม่วง), โมเมนต์ดัดพลิกคว่ำคู่ควบ Mu (ส้ม/ชมพู) และแรงดึงงัดหัวโบลต์รายตัว (ลูกศรแดง)")
    
    # รันการวาดภาพ 3 มิติเชิงกลศาสตร์แบบสมบูรณ์
    fig_metric = generate_metric_3d(B, N, tp, d, bf, tw, tf, num_anchors, Y_length, tension_per_bolt_kn, edge_g, p_u_kn, v_u_kn, m_u_knm)
    st.plotly_chart(fig_metric, use_container_width=True)
