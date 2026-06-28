# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. DATABASE: THAILAND COMMERCIAL STANDARDS
# ================= ================= =================
# ความหนาแผ่นเหล็กหนาที่มีจำหน่ายจริงในตลาดไทย (มิลลิเมตร)
THAI_PLATE_THICKNESSES = {
    "9 mm (~3/8\")": 9.0,
    "12 mm (~1/2\")": 12.0,
    "16 mm (~5/8\")": 16.0,
    "19 mm (~3/4\")": 19.0,
    "22 mm (~7/8\")": 22.0,
    "25 mm (~1\")": 25.0,
    "28 mm (~1-1/8\")": 28.0,
    "32 mm (~1-1/4\")": 32.0,
    "38 mm (~1-1/2\")": 38.0,
    "40 mm (~1-5/8\")": 40.0,
    "50 mm (~2\")": 50.0
}

# สลักเกลียวฝังเกรดทั่วไปในไทย (J-Bolt/L-Bolt เกรด SS400 / Grade 4.6, Fu = 400 MPa ~ 58 ksi)
THAI_ANCHOR_BOLTS = {
    "M16 (เส้นผ่านศูนย์กลาง 16 มม.)": {"dia_in": 0.630, "area_in2": 0.312, "F_nt": 43.5, "F_nv": 27.0},
    "M20 (เส้นผ่านศูนย์กลาง 20 มม.)": {"dia_in": 0.787, "area_in2": 0.487, "F_nt": 43.5, "F_nv": 27.0},
    "M24 (เส้นผ่านศูนย์กลาง 24 มม.)": {"dia_in": 0.945, "area_in2": 0.701, "F_nt": 43.5, "F_nv": 27.0},
    "M30 (เส้นผ่านศูนย์กลาง 30 มม.)": {"dia_in": 1.181, "area_in2": 1.096, "F_nt": 43.5, "F_nv": 27.0},
    "M36 (เส้นผ่านศูนย์กลาง 36 มม.)": {"dia_in": 1.417, "area_in2": 1.577, "F_nt": 43.5, "F_nv": 27.0}
}

st.set_page_config(page_title="AISC-Thai Base Plate Engine", layout="wide")

# คอนโทรลสไตล์ UI ให้ดูสะอาด เป็นสากลแบบโปรแกรมวิศวกรรมชั้นนำ
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .metric-card { background-color: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #e9ecef; text-align: center; }
    .step-header { background-color: #0f4c81; color: white; padding: 8px 15px; border-radius: 4px; margin-top: 15px; margin-bottom: 10px; font-weight: bold; }
    .recommend-box { background-color: #e3f2fd; padding: 10px 15px; border-radius: 5px; border-left: 5px solid #2196f3; margin-bottom: 12px; font-size: 0.95rem; }
    .warning-box { background-color: #fff3e0; padding: 10px 15px; border-radius: 5px; border-left: 5px solid #ff9800; margin-bottom: 12px; font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ AISC-Thai Base Plate Professional Engine")
st.caption("ระบบคำนวณจุดต่อเสาเหล็กและสลักเกลียวฝังตามพฤติกรรมจริง ร่วมกับวัสดุก่อสร้างที่มีจำหน่ายในประเทศไทย")

# ================= ================= =================
# 2. IMPROVED 3D VISUALIZATION GRAPHICS
# ================= ================= =================
def generate_engineering_3d_model(B, N, tp_in, col_d, col_bf, num_anchors, Y_length, edge_g=2.0):
    fig = go.Figure()

    # 1. คอนกรีตตอม่อ (Pedestal Base) - ปรับสีให้ดูเป็นคอนกรีตจริง
    fig.add_trace(go.Mesh3d(
        x=[-B*0.75, B*0.75, B*0.75, -B*0.75, -B*0.75, B*0.75, B*0.75, -B*0.75],
        y=[-N*0.75, -N*0.75, N*0.75, N*0.75, -N*0.75, -N*0.75, N*0.75, N*0.75],
        z=[-15, -15, -15, -15, 0, 0, 0, 0],
        color='rgb(210, 215, 219)', opacity=0.4, name='Concrete Pedestal'
    ))

    # 2. แผ่นฐานเหล็ก (Base Plate) - สีเหล็กเทาเข้มขัดเงา
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp_in, tp_in, tp_in, tp_in],
        color='rgb(70, 80, 95)', opacity=0.95, name='Base Plate'
    ))

    # 3. เสาเหล็กรูปพรรณ H-Beam (มิติจริง)
    tw, tf = 0.375, 0.50
    # Left Flange
    fig.add_trace(go.Mesh3d(x=[-col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2, -col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp_in, tp_in, tp_in, tp_in, tp_in+15, tp_in+15, tp_in+15, tp_in+15], color='rgb(40, 45, 55)', name='H-Column'))
    # Right Flange
    fig.add_trace(go.Mesh3d(x=[col_d/2-tf, col_d/2, col_d/2, col_d/2-tf, col_d/2-tf, col_d/2, col_d/2, col_d/2-tf],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp_in, tp_in, tp_in, tp_in, tp_in+15, tp_in+15, tp_in+15, tp_in+15], color='rgb(40, 45, 55)', showlegend=False))
    # Web
    fig.add_trace(go.Mesh3d(x=[-col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf, -col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf],
                            y=[-tw/2, -tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2],
                            z=[tp_in, tp_in, tp_in, tp_in, tp_in+15, tp_in+15, tp_in+15, tp_in+15], color='rgb(40, 45, 55)', showlegend=False))

    # 4. แนวรอยเชื่อมฟิลเล็ต (Weld Path)
    fig.add_trace(go.Scatter3d(
        x=[-col_d/2, col_d/2, col_d/2, -col_d/2, -col_d/2], y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2], z=[tp_in+0.05]*5,
        mode='lines', line=dict(color='rgb(255, 215, 0)', width=5), name='Fillet Weld'
    ))

    # 5. สลักเกลียวฝัง (Anchor Bolts Dynamic Arrangement)
    ex, ey = (B/2) - edge_g, (N/2) - edge_g
    if num_anchors == 4:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)]
    elif num_anchors == 6:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey)]
    else:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey), (-ex, 0), (ex, 0)]

    for idx, (bx, by) in enumerate(coords):
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-10, tp_in+2], mode='lines+markers',
            marker=dict(size=5, color='rgb(180, 40, 40)'), line=dict(color='rgb(220, 50, 50)', width=6),
            name='Anchor Bolt' if idx == 0 else '', showlegend=True if idx == 0 else False
        ))

    # 6. พื้นที่รับแรงอัดลิ่มคอนกรีตจริง (Effective Stress Zone)
    if Y_length > 0:
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2],
            z=[0, 0, 0, 0, -1.0, -1.0, -1.0, -1.0], color='rgba(255, 120, 0, 0.45)', name='Concrete Compression Block'
        ))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='B (X-Axis) [in]'), yaxis=dict(title='N (Y-Axis) [in]'), zaxis=dict(title='Z [in]'),
            aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.0))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=520
    )
    return fig

# ================= ================= =================
# 3. TWO-COLUMN LAYOUT AND INTERACTIVE WIZARD
# ================= ================= =================
ui_left, ui_right = st.columns([1.1, 0.9])

with ui_left:
    # -------------------------------------------------
    # STEP 1: BOUNDARY CONDITIONS
    # -------------------------------------------------
    st.markdown("<div class='step-header'>📍 STEP 1: น้ำหนักบรรทุกที่ฐานเสา & วัสดุเริ่มต้น</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        p_u = st.number_input("แรงกดใช้งาน, Pu (kips)", min_value=1.0, value=140.0, step=10.0)
        v_u = st.number_input("แรงเฉือนใช้งาน, Vu (kips)", min_value=0.0, value=22.0, step=2.0)
        m_u = st.number_input("โมเมนต์ดัดใช้งาน, Mu (kip-in)", min_value=0.0, value=480.0, step=40.0)
    with c2:
        col_d = st.number_input("ความลึกเสาเหล็ก d (นิ้ว)", min_value=4.0, value=10.0, step=0.25)
        col_bf = st.number_input("ความกว้างเสาเหล็ก bf (นิ้ว)", min_value=4.0, value=10.0, step=0.25)
        fc_prime = st.number_input("กำลังอัดคอนกรีต fc' (ksi) [เช่น 240 ksc -> 3.4 ksi]", min_value=2.0, value=3.5, step=0.5)
        fy_plate = st.number_input("กำลังคราดแผ่นเหล็ก Fy (ksi) [SS400 = 36 ksi]", value=36.0)

    # -------------------------------------------------
    # STEP 2: BASE PLATE GEOMETRY & THICKNESS (THAI STANDARDS)
    # -------------------------------------------------
    st.markdown("<div class='step-header'>📐 STEP 2: ขนาดและระดับความหนาแผ่นฐานเหล็ก (มอก. / ตลาดไทย)</div>", unsafe_allow_html=True)
    
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_prime
    a_min_req = p_u / f_p_max
    rec_B = col_bf + 4.0
    rec_N = col_d + 4.0
    
    st.markdown(f"""
    <div class='recommend-box'>
    💡 <b>ข้อเสนอแนะจากระบบ:</b><br>
    - คอนกรีตต้องการพื้นที่รองรับไม่น้อยกว่า <b>{round(a_min_req, 1)} ตร.นิ้ว</b><br>
    - เพื่อให้ครอบคลุมหน้าตัดเสาเหล็ก ควรใช้ขนาดอย่างน้อย: <b>B = {rec_B}\" และ N = {rec_N}\"</b>
    </div>
    """, unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        B = st.number_input("👉 กำหนดความกว้างจริง B (นิ้ว)", min_value=float(col_bf), value=float(rec_B), step=0.5)
    with c4:
        N = st.number_input("👉 กำหนดความยาวจริง N (นิ้ว)", min_value=float(col_d), value=float(rec_N), step=0.5)

    # คำนวณความเยื้องศูนย์และระยะลิ่มแรงกดเชิงวิศวกรรมจริง
    ecc = m_u / p_u if p_u > 0 else 0.0
    kern = N / 6.0
    edge_g = 2.0
    f_dist = (N / 2.0) - edge_g
    
    Y_length = 0.0
    t_req_min = 0.0
    bearing_stress_actual = 0.0
    tension_total = 0.0

    if ecc <= kern:
        # Small Eccentricity
        bearing_stress_actual = (p_u / (B * N)) * (1.0 + (6.0 * ecc / N))
        Y_length = N
        m = (N - 0.95 * col_d) / 2.0
        n = (B - 0.80 * col_bf) / 2.0
        n_prime = math.sqrt(col_d * col_bf) / 4.0
        l_crit = max(max(m, n), n_prime)
        t_req_min = l_crit * math.sqrt((2.0 * p_u) / (0.90 * fy_plate * B * N))
    else:
        # Large Eccentricity (เกิดคานงัดดึงนอต)
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
            
        m = (N - 0.95 * col_d) / 2.0
        if Y_length >= m:
            t_req_min = m * math.sqrt((2.0 * bearing_stress_actual) / (0.90 * fy_plate))
        else:
            t_req_min = math.sqrt((4.0 * tension_total * (f_dist - col_d/2.0)) / (0.90 * fy_plate * B))

    # ส่วนเลือกความหนาแผ่นเหล็กตามที่มีขายจริงในไทย
    st.markdown(f"**ความหนาขั้นต่ำที่คำนวณได้ทางวิศวกรรม:** <span class='math-text'>{round(t_req_min, 3)} นิ้ว</span> (~{round(t_req_min * 25.4, 1)} มม.)", unsafe_allow_html=True)
    selected_thickness_label = st.selectbox("👉 เลือกความหนาเหล็กแผ่นที่ใช้จริง (ตามขนาดตลาดประเทศไทยในหน่วย mm):", list(THAI_PLATE_THICKNESSES.keys()), index=2)
    tp_mm = THAI_PLATE_THICKNESSES[selected_thickness_label]
    tp_in = tp_mm / 25.4 # แปลงกลับไปเป็นนิ้วเพื่อใช้ในสมการและโมเดล 3D

    # -------------------------------------------------
    # STEP 3: WELD DESIGN
    # -------------------------------------------------
    st.markdown("<div class='step-header'>⚡ STEP 3: ขนาดรอยเชื่อมขาเสา (Fillet Weld)</div>", unsafe_allow_html=True)
    weld_length_total = (4.0 * col_bf) + (2.0 * col_d) - (2.0 * 0.375)
    s_weld_group = (col_bf * col_d) + (col_d**2 / 3.0) 
    
    # เช็กขนาดรอยเชื่อมขั้นต่ำตามความหนาเพลตจริง (AISC J2.4)
    if tp_in <= 0.25: w_min_rec = 2
    elif tp_in <= 0.50: w_min_rec = 3
    elif tp_in <= 0.75: w_min_rec = 4
    else: w_min_rec = 5
    
    st.markdown(f"<div class='recommend-box'>💡 <b>AISC J2.4 Minimum Weld Size:</b> แผ่นเหล็กหนา {tp_mm} มม. ต้องใช้รอยเชื่อมขนาดไม่ต่ำกว่า <b>{w_min_rec}/16\"</b></div>", unsafe_allow_html=True)
    base_weld_size = st.slider("👉 กำหนดขนาดรอยเชื่อมจริง (หน่วย 1/16 นิ้ว):", min_value=2, max_value=12, value=int(max(w_min_rec, 5)))
    
    weld_demand = math.sqrt((p_u/weld_length_total + m_u/s_weld_group)**2 + (v_u/weld_length_total)**2)
    weld_capacity = 0.75 * 0.60 * 70.0 * 0.707 * (base_weld_size / 16.0)

    # -------------------------------------------------
    # STEP 4: ANCHOR BOLTS CAPACITY INTERACTION (THAI METRIC SIZES)
    # -------------------------------------------------
    st.markdown("<div class='step-header'>🔩 STEP 4: ตรวจสอบและเลือกขนาดสลักเกลียวฝัง (Anchor Bolts)</div>", unsafe_allow_html=True)
    
    c5, c6 = st.columns(2)
    with c5:
        num_anchors = st.selectbox("👉 เลือกจำนวนสลักเกลียวที่ใช้ในจุดต่อ:", [4, 6, 8], index=0)
    with c6:
        selected_bolt_label = st.selectbox("👉 เลือกขนาดโบลต์มาตรฐานไทย (Metric):", list(THAI_ANCHOR_BOLTS.keys()), index=1)
        
    bolt_data = THAI_ANCHOR_BOLTS[selected_bolt_label]
    
    # คำนวณความต้องการ (Demands) ต่อนอตหนึ่งตัว
    tension_per_bolt = tension_total / (num_anchors / 2) if tension_total > 0 else 0.0
    shear_per_bolt = v_u / num_anchors
    
    # คำนวณกำลังต้านทานจริง (Design Capacity) ตามมาตรฐาน AISC 360-16 Chapter J
    phi_b_bolt = 0.75
    nominal_tensile_capacity = phi_b_bolt * bolt_data["F_nt"] * bolt_data["area_in2"]
    nominal_shear_capacity = phi_b_bolt * bolt_data["F_nv"] * bolt_data["area_in2"]
    
    if tension_per_bolt > 0:
        st.markdown(f"""
        <div class='warning-box'>
        ⚠️ <b>สถานะแรงดึงวิกฤต:</b> โบลต์รับแรงดึงตัวละ <b>{round(tension_per_bolt, 2)} kips</b> | กำลังรับแรงดึงระบุของตัวโบลต์เหล็ก <b>{round(nominal_tensile_capacity, 2)} kips</b>
        </div>
        """, unsafe_allow_html=True)

# ================= ================= =================
# 4. VIEWPORT, VERIFICATION TABLES AND PROFESSIONAL LAYOUT
# ================= ================= =================
with ui_right:
    st.markdown("### 📊 AISC Structural Verification Matrix")
    st.caption("สรุปและตรวจสอบพฤติกรรมการรับแรงของจุดต่อเมื่อเทียบกับกำลังวัสดุจริง")

    # อัตราการใช้กำลังในแต่ละจุดวิกฤต (Utilization Ratios)
    bearing_util = (bearing_stress_actual / f_p_max) * 100 if f_p_max > 0 else 0
    plate_util = (t_req_min / tp_in) * 100 if tp_in > 0 else 0
    weld_util = (weld_demand / weld_capacity) * 100 if weld_capacity > 0 else 0
    bolt_tension_util = (tension_per_bolt / nominal_tensile_capacity) * 100 if nominal_tensile_capacity > 0 else 0
    bolt_shear_util = (shear_per_bolt / nominal_shear_capacity) * 100 if nominal_shear_capacity > 0 else 0

    verification_table = [
        {
            "Limit State (จุดตรวจสอบวิกฤต)": "1. คอนกรีตรับแรงบดอัด (Bearing)",
            "Demand": f"{round(bearing_stress_actual, 2)} ksi",
            "Capacity (φRn)": f"{round(f_p_max, 2)} ksi",
            "Ratio (%)": f"{round(bearing_util, 1)}%",
            "Result": "✅ PASS" if bearing_stress_actual <= f_p_max else "❌ FAIL"
        },
        {
            "Limit State (จุดตรวจสอบวิกฤต)": "2. ความหนาแผ่นเพลต (Plate Bending)",
            "Demand": f"{round(t_req_min, 3)} in",
            "Capacity (φRn)": f"{round(tp_in, 3)} in",
            "Ratio (%)": f"{round(plate_util, 1)}%",
            "Result": "✅ PASS" if t_req_min <= tp_in else "❌ FAIL"
        },
        {
            "Limit State (จุดตรวจสอบวิกฤต)": "3. แรงเค้นในรอยเชื่อมขาเสา (Weld)",
            "Demand": f"{round(weld_demand, 2)} k/in",
            "Capacity (φRn)": f"{round(weld_capacity, 2)} k/in",
            "Ratio (%)": f"{round(weld_util, 1)}%",
            "Result": "✅ PASS" if weld_demand <= weld_capacity else "❌ FAIL"
        },
        {
            "Limit State (จุดตรวจสอบวิกฤต)": "4. โบลต์รับแรงดึง (Bolt Tension)",
            "Demand": f"{round(tension_per_bolt, 2)} kips",
            "Capacity (φRn)": f"{round(nominal_tensile_capacity, 2)} kips",
            "Ratio (%)": f"{round(bolt_tension_util, 1)}%",
            "Result": "✅ PASS" if tension_per_bolt <= nominal_tensile_capacity else "❌ FAIL"
        },
        {
            "Limit State (จุดตรวจสอบวิกฤต)": "5. โบลต์รับแรงเฉือน (Bolt Shear)",
            "Demand": f"{round(shear_per_bolt, 2)} kips",
            "Capacity (φRn)": f"{round(nominal_shear_capacity, 2)} kips",
            "Ratio (%)": f"{round(bolt_shear_util, 1)}%",
            "Result": "✅ PASS" if shear_per_bolt <= nominal_shear_capacity else "❌ FAIL"
        }
    ]
    st.table(verification_table)

    # แผงตรวจสอบสรุปสถานะความปลอดภัยสูงสุดของระบบ (Max Interaction)
    max_util = max([bearing_util, plate_util, weld_util, bolt_tension_util, bolt_shear_util])
    if max_util > 100:
        st.error(f"❌ โครงสร้างไม่ปลอดภัย (OVERSTRESSED): อัตราส่วนรับแรงสูงสุดทะลุไปที่ {round(max_util, 1)}% กรุณาเพิ่มขนาดหน้าตัดหรือความหนาแผ่นเหล็ก")
    else:
        st.success(f"✅ โครงสร้างผ่านเกณฑ์ความปลอดภัยสูงสุด (SAFE): อัตราการใช้กำลังสูงสุดของจุดต่ออยู่ที่ {round(max_util, 1)}%")

    st.markdown("---")
    st.markdown("### 🧊 Live 3D Mechanical Spatial Model")
    st.caption("ระนาบแผ่นสีส้มใต้เพลตคือระยะลิ่มแรงกดจริงบนคอนกรีต ($Y$) ที่เปลี่ยนรูปร่างไปตามความเยื้องศูนย์ของแรงแบบเรียลไทม์")
    
    # เรนเดอร์กราฟิกโมเดล 3 มิติเชิงกลศาสตร์แบบสมบูรณ์
    fig_model = generate_engineering_3d_model(B, N, tp_in, col_d, col_bf, num_anchors, Y_length, edge_g)
    st.plotly_chart(fig_model, use_container_width=True)
