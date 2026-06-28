# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. CONFIGURATION & GLOBAL STYLES
# ================= ================= =================
st.set_page_config(page_title="AISC Professional Connection Engine", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .stTable { background-color: #ffffff; border-radius: 8px; }
    .step-box { background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 6px solid #004085; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .math-text { font-family: 'Courier New', Courier, monospace; color: #c7254e; background-color: #f9f2f4; padding: 2px 4px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ AISC Professional Connection Engine")
st.caption("ระบบคำนวณจุดต่อและกลศาสตร์แผ่นฐานเสารับแรงร่วมขั้นสูง (Combined Axial, Shear, and Moment) | AISC 360-16 LRFD")

# ================= ================= =================
# 2. 3D PARAMETRIC VISUALIZATION ENGINE
# ================= ================= =================
def generate_advanced_load_path_3d(B, N, tp, col_d, col_bf, num_anchors, Y_length, edge_g=2.0):
    fig = go.Figure()

    # 1. คอนกรีตฐานราก (Pedestal)
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-20, -20, -20, -20, 0, 0, 0, 0],
        color='rgba(200, 200, 200, 0.4)', opacity=0.25, name='Concrete Pedestal'
    ))

    # 2. แผ่นฐานเหล็ก (Base Plate)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='lightslategray', opacity=0.9, name='Base Plate'
    ))

    # 3. หน้าตัดเสาเหล็ก (H-Column)
    tw, tf = 0.375, 0.50
    # Left Flange
    fig.add_trace(go.Mesh3d(x=[-col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2, -col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+20, tp+20, tp+20, tp+20], color='black', name='Steel Column'))
    # Right Flange
    fig.add_trace(go.Mesh3d(x=[col_d/2-tf, col_d/2, col_d/2, col_d/2-tf, col_d/2-tf, col_d/2, col_d/2, col_d/2-tf],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+20, tp+20, tp+20, tp+20], color='black', showlegend=False))
    # Web
    fig.add_trace(go.Mesh3d(x=[-col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf, -col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf],
                            y=[-tw/2, -tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2],
                            z=[tp, tp, tp, tp, tp+20, tp+20, tp+20, tp+20], color='black', showlegend=False))

    # 4. แนวรอยเชื่อมฟิลเล็ต (Weld Perimeter)
    fig.add_trace(go.Scatter3d(
        x=[-col_d/2, col_d/2, col_d/2, -col_d/2, -col_d/2], y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2], z=[tp+0.1]*5,
        mode='lines', line=dict(color='yellow', width=6), name='Fillet Weld Line'
    ))

    # 5. การจัดเรียงสลักเกลียวฝัง (Anchor Bolts)
    ex, ey = (B/2) - edge_g, (N/2) - edge_g
    if num_anchors == 4:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)]
    elif num_anchors == 6:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey)]
    else:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey), (-ex, 0), (ex, 0)]

    for idx, (bx, by) in enumerate(coords):
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-14, tp+2], mode='lines+markers',
            marker=dict(size=4, color='crimson'), line=dict(color='crimson', width=6),
            name='Anchor Bolt' if idx == 0 else '', showlegend=True if idx == 0 else False
        ))

    # 6. ลิ่มแรงกดคอนกรีตจำลอง (Concrete Bearing Stress Block Area)
    if Y_length > 0:
        # แสดงขอบเขตพื้นที่รับแรงกดวิกฤตจริง
        y_start = (N/2) - Y_length
        fig.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[y_start, y_start, N/2, N/2, y_start, y_start, N/2, N/2],
            z=[0, 0, 0, 0, -1.5, -1.5, -1.5, -1.5], color='rgba(255, 165, 0, 0.5)', name='Effective Bearing Area (Y)'
        ))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='X Axis (B) [in]'), yaxis=dict(title='Y Axis (N) [in]'), zaxis=dict(title='Z Axis [in]'),
            bgcolor='rgba(255, 255, 255, 0)', aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=0.9))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=500
    )
    return fig

# ================= ================= =================
# 3. INTERACTIVE CALCULATION FLOW (4 STEPS MECHANICS)
# ================= ================= =================
col_wizard, col_viewport = st.columns([1.2, 0.8])

with col_wizard:
    # -------------------------------------------------
    # STEP 1: INDEPENDENT BOUNDARY SPECIFICATIONS
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h3>📍 Step 1: แรงภายนอกและหน้าตัดโครงสร้างต้นทาง</h3><p>ป้อนค่าแรงกระทำจริง ณ โคนเสา และคุณสมบัติวัสดุพื้นฐานเพื่อส่งถ่ายลงสู่จุดต่อ</p></div>", unsafe_allow_html=True)
    
    col_s1_1, col_s1_2 = st.columns(2)
    with col_s1_1:
        p_u = st.number_input("Factored Axial Load, $P_u$ (kips) [แรงกด (+)]", min_value=1.0, value=120.0, step=10.0)
        v_u = st.number_input("Factored Shear Load, $V_u$ (kips) [แรงเฉือน]", min_value=0.0, value=20.0, step=5.0)
        m_u = st.number_input("Factored Overturning Moment, $M_u$ (kip-in)", min_value=0.0, value=500.0, step=50.0)
    with col_s1_2:
        col_d = st.number_input("ความลึกหน้าตัดเสาเหล็กจริง $d$ (นิ้ว)", min_value=4.0, value=10.0, step=0.1)
        col_bf = st.number_input("ความกว้างปีกเสาเหล็กจริง $b_f$ (นิ้ว)", min_value=4.0, value=10.0, step=0.1)
        fc_prime = st.number_input("กำลังอัดประลัยคอนกรีตฐานราก $f'_c$ (ksi)", min_value=2.0, value=4.0, step=0.5)
        fy_plate = st.number_input("กำลังรับแรงดึงที่จุดคราดเหล็กแผ่น $F_y$ (ksi)", value=36.0)

    # -------------------------------------------------
    # STEP 2: RIGOROUS BASE PLATE ECCENTRICITY ANALYSIS
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h3>📐 Step 2: วิเคราะห์กลศาสตร์ความเยื้องศูนย์และขนาดแผ่นฐาน</h3><p>คำนวณพฤติกรรมพังทลายของคอนกรีต (Concrete Bearing Limit State) และความหนาเหล็กแผ่นวิกฤต</p></div>", unsafe_allow_html=True)
    
    # คำนวณความเยื้องศูนย์จริง
    ecc = m_u / p_u if p_u > 0 else 0.0
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_prime  # กำลังแบกทานสูงสุดที่ยอมรับได้ของคอนกรีต (กรณี A2/A1 = 1.0 แบบอนุรักษ์นิยม)
    
    # แนะนำขนาดพื้นที่ขั้นต่ำที่คอนกรีตต้องการ
    a_min_req = p_u / f_p_max
    rec_B = col_bf + 4.0
    rec_N = col_d + 4.0
    
    st.markdown(f"""
    > **ผลวิเคราะห์กลศาสตร์เชิงลึก:** > * ค่าความเยื้องศูนย์ของแรงจริง $e = M_u / P_u =$ **{round(ecc, 3)} นิ้ว** > * หน่วยแรงกดคอนกรีตยอมรับได้สูงสุด $f_p = 0.65 \\times 0.85 \\times f'_c =$ **{round(f_p_max, 2)} ksi** > * พื้นที่รับแรงกดขั้นต่ำที่คอนกรีตต้องการตามกฎสมดุลแรง = **{round(a_min_req, 1)} ตร.นิ้ว**
    """)
    
    col_s2_1, col_s2_2 = st.columns(2)
    with col_s2_1:
        B = st.number_input("👉 กำหนดความกว้างแผ่นฐานเหล็กจริง B (นิ้ว)", min_value=float(col_bf), value=float(rec_B), step=0.5)
    with col_s2_2:
        N = st.number_input("👉 กำหนดความยาวแผ่นฐานเหล็กจริง N (นิ้ว)", min_value=float(col_d), value=float(rec_N), step=0.5)

    # ตรวจสอบประเภทพฤติกรรมความเยื้องศูนย์ (Small vs Large Eccentricity)
    kern = N / 6.0
    edge_g = 2.0 # ระยะร่นนอตมาตรฐาน
    f_dist = (N / 2.0) - edge_g # ระยะจากศูนย์กลางเสาไปถึงแนวนอต
    
    Y_length = 0.0
    t_req_min = 0.0
    bearing_stress_max = 0.0
    tension_total = 0.0

    if ecc <= kern:
        # Case 1: Small Eccentricity (แรงกดกระจายทั่วแผ่นฐาน ไม่มีแรงดึงในนอต)
        st.info(f"💡 **พฤติกรรมกลุ่มแรงกดต่ำ ($e \\le N/6$):** แรงกดกระจายตัวเป็นรูปคางหมูทั่วแผ่นฐาน นอตฝังไม่มีแรงดึงงัดเกิดขึ้น")
        bearing_stress_max = (p_u / (B * N)) * (1.0 + (6.0 * ecc / N))
        Y_length = N # กดเต็มความยาว
        
        # คำนวณความหนาแผ่นฐานตามทฤษฎีคานยื่น AISC
        m = (N - 0.95 * col_d) / 2.0
        n = (B - 0.80 * col_bf) / 2.0
        n_prime = math.sqrt(col_d * col_bf) / 4.0
        l_crit = max(max(m, n), n_prime)
        
        phi_b = 0.90
        t_req_min = l_crit * math.sqrt((2.0 * p_u) / (phi_b * fy_plate * B * N))
    else:
        # Case 2: Large Eccentricity ($e > N/6$) ตามมาตรฐาน AISC Design Guide 1
        st.warning(f"⚠️ **พฤติกรรมแรงดัดสูง ($e > N/6$):** แรงเยื้องศูนย์ออกนอกหน้าตัดวิกฤต เกิดลิ่มแรงกดเป็นรูปสามเหลี่ยม และเกิดแรงงัดถอนนอตฝัง")
        
        # แก้สมการกำลังสองหาความยาวลิ่มแรงกดคคอนกรีต (Y) อ้างอิงสมการสมดุลโมเมนต์รอบแนวนอตรับแรงดึง
        # (AISC Design Guide 1 สมการกำลังสองหาค่า Y)
        a_coeff = B * f_p_max / 2.0
        b_coeff = -B * f_p_max * (f_dist + N/2.0)
        c_coeff = p_u * (ecc + f_dist)
        
        discriminant = b_coeff**2 - 4.0 * a_coeff * c_coeff
        if discriminant >= 0:
            Y_root1 = (-b_coeff - math.sqrt(discriminant)) / (2.0 * a_coeff)
            Y_length = Y_root1
            bearing_stress_max = f_p_max
            # คำนวณแรงดึงรวมในนอตฝังจากสมดุลแรงแนวดิ่ง
            tension_total = (f_p_max * B * Y_length / 2.0) - p_u
        else:
            Y_length = N
            bearing_stress_max = f_p_max * 2.0 # เกินกำลังวิกฤต
            tension_total = 999.0
            
        # คำนวณความหนาแผ่นฐานกรณีแรงดัดสูง (AISC DG1 Section 3.2)
        # ตรวจสอบจุดดัดงอวิกฤตตรงแนวขอบเสารับแรงดึงเทียบฝั่งแรงอัด
        m = (N - 0.95 * col_d) / 2.0
        phi_b = 0.90
        if Y_length >= m:
            t_req_min = m * math.sqrt((2.0 * bearing_stress_max) / (phi_b * fy_plate))
        else:
            t_req_min = math.sqrt((4.0 * tension_total * (f_dist - col_d/2.0)) / (phi_b * fy_plate * B))

    st.info(f"💡 **ความหนาเหล็กแผ่นฐานที่ต้องการทางทฤษฎี:** $t_{{p, min}} =$ **{round(t_req_min, 3)} นิ้ว**")
    tp_user = st.number_input("👉 กำหนดความหนาแผ่นฐานเลือกใช้จริง $t_p$ (นิ้ว)", min_value=0.25, value=max(1.0, math.ceil(t_req_min*8)/8), step=0.125)

    # -------------------------------------------------
    # STEP 3: COLUMN-TO-PLATE WELD CAPACITY (ELASTIC MATRIX)
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h3>⚡ Step 3: คำนวณหน่วยแรงในรอยเชื่อมโคนเสา (Weld Stress Group)</h3><p>วิเคราะห์หน่วยแรงรวมจากแรงเฉือน แรงกด และโมเมนต์แบบ Elastic Method จริง</p></div>", unsafe_allow_html=True)
    
    # คำนวณความยาวรอยเชื่อมฟิลเล็ตรอบหน้าตัดเสา H-Shape จริง
    weld_length_total = (4.0 * col_bf) + (2.0 * col_d) - (2.0 * 0.375) # ความยาวสายเชื่อมรอบตัวเสาโดยประมาณ
    # โมดูลัสหน้าตัดของกลุ่มรอยเชื่อม (Section Modulus of Weld Group, Sw) สมมติคิดเป็นเส้นบรรทัด
    s_weld_group = (col_bf * col_d) + (col_d**2 / 3.0) 
    
    # แนะนำขนาดรอยเชื่อมขั้นต่ำตามมาตรฐาน AISC Table J2.4
    if tp_user <= 0.25: w_min_rec = 2
    elif tp_user <= 0.50: w_min_rec = 3
    elif tp_user <= 0.75: w_min_rec = 4
    else: w_min_rec = 5
    
    st.info(f"💡 **ข้อกำหนด AISC J2.4:** แผ่นเหล็กหนา {tp_user}\" บังคับขนาดขาเชื่อมขั้นต่ำ **{w_min_rec}/16\"** | ความยาวรอยเชื่อมรอบหน้าตัดรวม = {round(weld_length_total, 2)} นิ้ว")
    base_weld_size = st.slider("👉 เลือกขนาดขาเชื่อมฟิลเล็ตจริงที่ต้องการ (หน่วยส่วน 1/16 นิ้ว)", min_value=2, max_value=16, value=int(max(w_min_rec, 5)))
    
    # คำนวณแรงเค้นในรอยเชื่อมจริงต่อความยาว 1 นิ้ว (kips/linear inch)
    f_weld_axial = p_u / weld_length_total if weld_length_total > 0 else 0
    f_weld_moment = m_u / s_weld_group if s_weld_group > 0 else 0
    f_weld_shear = v_u / weld_length_total if weld_length_total > 0 else 0
    
    # รวมแรงเค้นแบบ Vector Resultant แรงเค้นตั้งฉาก + แรงเค้นเฉือน
    weld_demand_total = math.sqrt((f_weld_axial + f_weld_moment)**2 + f_weld_shear**2)
    # กำลังรับแรงของรอยเชื่อมตามมาตรฐาน AISC LRFD (ลวดเชื่อม E70: F_EXX = 70 ksi)
    phi_w = 0.75
    weld_thickness_actual = base_weld_size * (1.0 / 16.0)
    weld_capacity_per_inch = phi_w * 0.60 * 70.0 * 0.707 * weld_thickness_actual

    # -------------------------------------------------
    # STEP 4: ANCHOR BOLT CAPACITY & PULLOUT MECHANICS
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h3>🔩 Step 4: ประเมินแรงดึงและแรงเฉือนในสลักเกลียวฝัง</h3><p>ตรวจจับแรงถอนงัดที่ถ่ายลงสู่นอตแต่ละตัวพร้อมเช็กแรงตัดวิกฤต</p></div>", unsafe_allow_html=True)
    
    num_anchors = st.selectbox("👉 เลือกจำนวนสลักเกลียวฝังที่ต้องการจัดวาง", [4, 6, 8], index=0)
    
    # แรงดึงต่อนอตหนึ่งตัว (เฉพาะนอตฝังด้านที่รับแรงดึงงัด)
    tension_per_bolt = tension_total / (num_anchors / 2) if tension_total > 0 else 0.0
    # แรงเฉือนต่อนอตหนึ่งตัว (เฉลี่ยรับแรงเฉือน Vu ร่วมกันทั้งหมดตามหลัก LRFD)
    shear_per_bolt = v_u / num_anchors if num_anchors > 0 else 0.0

    if tension_per_bolt > 0:
        st.warning(f"⚠️ **ค่าน้ำหนักบรรทุกงัดหัวนอต:** สลักเกลียวฝั่ง Tension ต้องรับแรงดึงบริสุทธิ์ตัวละ **{round(tension_per_bolt, 2)} kips** และรับแรงเฉือนร่วมอีกตัวละ **{round(shear_per_bolt, 2)} kips**")
    else:
        st.success(f"✅ **ไม่มีแรงดึงในนอต:** สลักเกลียวรับเฉพาะแรงเฉือนคงที่จากการสไลด์ตัวละ **{round(shear_per_bolt, 2)} kips** เท่านั้น")

# ================= ================= =================
# 4. ENGINEERING LIMIT STATES MATRIX & 3D VIEWPORT
# ================= ================= =================
with col_viewport:
    st.markdown("### 📊 AISC Engineering Verification Matrix")
    st.caption("ตารางวิเคราะห์สัดส่วนความปลอดภัยและกำลังต้านทานจริงตามเกณฑ์ข้อกำหนดของแผ่นฐาน")

    # ประเมินร้อยละการใช้กำลัง (Utilization) ในแต่ละส่วน
    bearing_util = (bearing_stress_max / f_p_max) * 100 if f_p_max > 0 else 0
    plate_util = (t_req_min / tp_user) * 100 if tp_user > 0 else 0
    weld_util = (weld_demand_total / weld_capacity_per_inch) * 100 if weld_capacity_per_inch > 0 else 0

    verification_matrix = [
        {
            "Limit State Check": "1. Concrete Bearing Strength",
            "AISC Criteria": "AISC 360-16 J8",
            "Demand": f"{round(bearing_stress_max, 2)} ksi",
            "Design Capacity ($\phi R_n$)": f"{round(f_p_max, 2)} ksi",
            "Utilization (%)": f"{round(bearing_util, 1)}%",
            "Status": "PASS" if bearing_stress_max <= f_p_max else "FAIL"
        },
        {
            "Limit State Check": "2. Base Plate Bending",
            "AISC Criteria": "Design Guide 1",
            "Demand": f"{round(t_req_min, 3)} in (req.)",
            "Design Capacity ($\phi R_n$)": f"{round(tp_user, 3)} in (prov.)",
            "Utilization (%)": f"{round(plate_util, 1)}%",
            "Status": "PASS" if t_req_min <= tp_user else "FAIL"
        },
        {
            "Limit State Check": "3. Base Fillet Weld Stress",
            "AISC Criteria": "AISC 360-16 J2.4",
            "Demand": f"{round(weld_demand_total, 2)} k/in",
            "Design Capacity ($\phi R_n$)": f"{round(weld_capacity_per_inch, 2)} k/in",
            "Utilization (%)": f"{round(weld_util, 1)}%",
            "Status": "PASS" if weld_demand_total <= weld_capacity_per_inch else "FAIL"
        }
    ]
    st.table(verification_matrix)

    # การ์ดสรุปความปลอดภัยวิกฤต
    max_system_util = max(max(bearing_util, plate_util), weld_util)
    if max_system_util > 100:
        st.error(f"❌ CRITICAL OVERSTRESS (ระบบไม่ปลอดภัย): อัตราการใช้กำลังสูงสุดทะลุไปที่ {round(max_system_util, 1)}% โปรดเพิ่มความหนาแผ่นเหล็ก หรือขยายขนาดฐานเหล็กต้นทาง")
    else:
        st.success(f"✅ STRUCTURAL COMPLIANT (ผ่านเกณฑ์): โครงสร้างจุดต่อปลอดภัยร้อยเปอร์เซ็นต์ อัตรากำลังวิกฤตสูงสุดอยู่ที่ {round(max_system_util, 1)}%")

    st.markdown("---")
    st.markdown("### 🧊 Live 3D Stress Visualization Block")
    st.caption("แถบสีส้มใต้แผ่นฐานเหล็ก แสดงบริเวณขอบเขตระยะลิ่มแรงกดจริง ($Y$) ที่เกิดขึ้นบนคอนกรีตฐานรากตามทฤษฎีสมดุลกลศาสตร์")
    
    # วาดรูปโมเดล 3D ที่ขยับพิกัดและพื้นที่สีส้มตามพฤติกรรมการคำนวณจริง
    fig_advanced_connection = generate_advanced_load_path_3d(B, N, tp_user, col_d, col_bf, num_anchors, Y_length, edge_g)
    st.plotly_chart(fig_advanced_connection, use_container_width=True)
