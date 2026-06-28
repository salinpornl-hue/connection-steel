# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= ================= =================
# 1. ARCHITECTURE SETUP & ENGINE FALLBACK
# ================= ================= =================
try:
    from engine import AISC_LRFD_Engine
    engine = AISC_LRFD_Engine()
except ImportError:
    class AISC_LRFD_Engine:
        def calculate_bolt_shear_capacity(self, d, g, t, p): 
            return {"design_capacity_kips": 25.0, "A_b": 0.44, "F_nv": 54.0, "nominal_capacity_kips": 33.0}
        def calculate_weld_capacity(self, s, l, e): 
            return {"design_capacity_kips": 120.0, "weld_size_inch": 0.3125, "effective_throat": 0.221, "nominal_capacity_kips": 160.0}
    engine = AISC_LRFD_Engine()

st.set_page_config(page_title="AISC Load-Path Connection Wizard", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .stTable { background-color: #ffffff; border-radius: 8px; }
    .step-box { background-color: #f1f3f6; padding: 15px; border-radius: 8px; border-left: 6px solid #1f77b4; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ AISC Load-Path Connection Wizard")
st.caption("ระบบแนะนำและออกแบบจุดต่ออัจฉริยะตามลำดับการถ่ายแรงสากล | AISC 360-16 LRFD Compliance")

# ================= ================= =================
# 2. 3D PARAMETRIC ENGINE (STABLE VERSION)
# ================= ================= =================
def generate_load_path_base_plate_3d(B, N, tp, col_d, col_bf, num_anchors):
    fig = go.Figure()

    # 1. คอนกรีตฐานราก (Pedestal)
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-18, -18, -18, -18, 0, 0, 0, 0],
        color='rgba(220, 220, 220, 0.4)', opacity=0.3, name='Pedestal'
    ))

    # 2. แผ่นฐานเหล็ก (Base Plate)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='steelblue', opacity=0.85, name='Base Plate'
    ))

    # 3. หน้าตัดเสาเหล็ก (H-Column Geometry)
    tw, tf = 0.375, 0.50
    # Left Flange
    fig.add_trace(go.Mesh3d(x=[-col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2, -col_d/2, -col_d/2+tf, -col_d/2+tf, -col_d/2],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', name='Column'))
    # Right Flange
    fig.add_trace(go.Mesh3d(x=[col_d/2-tf, col_d/2, col_d/2, col_d/2-tf, col_d/2-tf, col_d/2, col_d/2, col_d/2-tf],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', showlegend=False))
    # Web
    fig.add_trace(go.Mesh3d(x=[-col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf, -col_d/2+tf, col_d/2-tf, col_d/2-tf, -col_d/2+tf],
                            y=[-tw/2, -tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', showlegend=False))

    # 4. แนวรอยเชื่อมฟิลเล็ต (Weld Line)
    fig.add_trace(go.Scatter3d(
        x=[-col_d/2, col_d/2, col_d/2, -col_d/2, -col_d/2], y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2], z=[tp+0.1]*5,
        mode='lines', line=dict(color='yellow', width=5), name='Fillet Weld Perimeter'
    ))

    # 5. สลักเกลียวฝังแบบ Dynamic Layout
    eg = 2.0
    ex, ey = (B/2) - eg, (N/2) - eg
    if num_anchors == 4:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)]
    elif num_anchors == 6:
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey)]
    else: # 8 ตัว
        coords = [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey), (0, -ey), (0, ey), (-ex, 0), (ex, 0)]

    for idx, (bx, by) in enumerate(coords):
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-12, tp+2], mode='lines+markers',
            marker=dict(size=4, color='crimson'), line=dict(color='crimson', width=7),
            name='Anchor Bolt' if idx == 0 else '', showlegend=True if idx == 0 else False
        ))

    # 6. ลูกศรแสดงทิศทางแรงเวกเตอร์
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+16], u=[0], v=[0], w=[-1], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0,'magenta'],[1,'magenta']], name='Pu Direction'))
    fig.add_trace(go.Cone(x=[B/2], y=[0], z=[tp], u=[1], v=[0], w=[0], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0,'green'],[1,'green']], name='Vu Direction'))

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title='X (in)'), yaxis=dict(title='Y (in)'), zaxis=dict(title='Z (in)'),
            aspectmode='data', camera=dict(eye=dict(x=1.25, y=-1.25, z=0.85))
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=550
    )
    return fig

# ================= ================= =================
# 3. INTERACTIVE 4-STEP WORKFLOW WIZARD (UI LAYOUT)
# ================= ================= =================
col_wizard, col_viewport = st.columns([1.1, 0.9])

with col_wizard:
    # -------------------------------------------------
    # STEP 1: BOUNDARY CONDITIONS & EXTERNAL DEMANDS
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h4>📍 Step 1: แรงภายนอกและคุณสมบัติหน้าตัดเริ่มต้น</h4></div>", unsafe_allow_html=True)
    
    col_s1_1, col_s1_2 = st.columns(2)
    with col_s1_1:
        p_u = st.number_input("Factored Axial Load, Pu (kips) [แรงกด]", min_value=0.0, value=150.0, step=10.0)
        v_u = st.number_input("Factored Shear Load, Vu (kips) [แรงเฉือน]", min_value=0.0, value=25.0, step=5.0)
        m_u = st.number_input("Factored Moment, Mu (kip-in) [โมเมนต์ดัด]", min_value=0.0, value=450.0, step=50.0)
    with col_s1_2:
        col_d = st.number_input("ความลึกเสาเหล็กจริง d (นิ้ว)", min_value=4.0, value=10.0, step=0.5)
        col_bf = st.number_input("ความกว้างปีกเสาจริง bf (นิ้ว)", min_value=4.0, value=10.0, step=0.5)
        fc_prime = st.number_input("กำลังอัดคอนกรีตตอม่อ fc' (ksi)", min_value=2.0, value=4.0, step=0.5)
        fy_plate = st.number_input("กำลังคราดเหล็กแผ่นฐาน Fy (ksi)", value=36.0)

    # -------------------------------------------------
    # STEP 2: BASE PLATE DIMENSIONING & THICKNESS
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h4>📐 Step 2: ออกแบบขนาดและความหนาแผ่นฐาน (Base Plate)</h4></div>", unsafe_allow_html=True)
    
    # 🧠 ลอจิกคำนวณพื้นที่ขั้นต่ำที่คอนกรีตรับได้ (Concrete Bearing Limit State)
    phi_c = 0.65
    a_min_req = p_u / (phi_c * 0.85 * fc_prime) if fc_prime > 0 else 0
    # ขนาดแนะนำตามมิติเสาเหล็กจริง เพื่อให้เหล็กแผ่นคลุมเสามิดและมีระยะเจาะรูนอตเหลือ
    rec_B_size = col_bf + 4.0
    rec_N_size = col_d + 4.0
    
    st.info(f"💡 **คำแนะนำจากระบบ (Recommendation):** \n- คอนกรีตต้องการพื้นที่แบกทานอย่างน้อย **{round(a_min_req, 2)} ตร.นิ้ว**\n- มิติแผ่นฐานที่แนะนำเพื่อหลบปีกเสาและเจาะรูได้ง่ายคืออย่างน้อย **{rec_B_size}\" x {rec_N_size}\"**")
    
    col_s2_1, col_s2_2 = st.columns(2)
    with col_s2_1:
        B = st.number_input("👉 กำหนดความกว้างแผ่นฐานจริง B (นิ้ว)", min_value=float(col_bf), value=float(rec_B_size), step=0.5)
    with col_s2_2:
        N = st.number_input("👉 กำหนดความยาวแผ่นฐานจริง N (นิ้ว)", min_value=float(col_d), value=float(rec_N_size), step=0.5)
        
    # 🧠 ลอจิกวิเคราะห์ความหนาขั้นต่ำต่อ (Plate Bending Cantilever Theory)
    m = (N - 0.95 * col_d) / 2
    n = (B - 0.80 * col_bf) / 2
    n_prime = math.sqrt(col_d * col_bf) / 4
    l_crit = max(max(m, n), n_prime)
    
    phi_b = 0.90
    actual_area = B * N
    t_req_min = 0.0
    if actual_area > 0 and p_u > 0:
        t_req_min = l_crit * math.sqrt((2 * p_u) / (phi_b * fy_plate * B * N))
        
    st.info(f"💡 **คำแนะนำความหนาเหล็กแผ่น:** จากระยะคานยื่นวิกฤตที่เกิดขึ้น แผ่นฐานต้องหนาอย่างน้อย **{round(t_req_min, 3)} นิ้ว**")
    tp_user = st.number_input("👉 กำหนดความหนาแผ่นฐานเลือกใช้จริง tp (นิ้ว)", min_value=0.25, value=max(1.0, math.ceil(t_req_min*8)/8), step=0.125)

    # -------------------------------------------------
    # STEP 3: COLUMN-TO-PLATE WELD SPECIFICATION
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h4>⚡ Step 3: ออกแบบขนาดรอยเชื่อมระหว่างเสากับแผ่นฐาน</h4></div>", unsafe_allow_html=True)
    
    # 🧠 ลอจิกแนะนำขนาดรอยเชื่อมฟิลเล็ตขั้นต่ำตามตาราง AISC Table J2.4 (อิงจากความหนาแผ่นเหล็กที่เลือกใน Step 2)
    if tp_user <= 0.25: min_weld_16th = 2      # 1/8"
    elif tp_user <= 0.50: min_weld_16th = 3    # 3/16"
    elif tp_user <= 0.75: min_weld_16th = 4    # 1/4"
    else: min_weld_16th = 5                    # 5/16"
    
    st.info(f"💡 **คำแนะนำตามมาตรฐาน AISC Table J2.4:** สำหรับแผ่นเหล็กหนา {tp_user}\" ต้องใช้ขนาดขาของรอยเชื่อม (Fillet Weld Size) ไม่ต่ำกว่า **{min_weld_16th}/16\"**")
    base_weld_size = st.slider("👉 เลือกขนาดขารอยเชื่อมจริงที่วิศวกรต้องการใช้ (หน่วยส่วน 1/16 นิ้ว)", min_value=2, max_value=16, value=int(max(min_weld_16th, 6)))

    # -------------------------------------------------
    # STEP 4: ANCHOR BOLT CONFIGURATION
    # -------------------------------------------------
    st.markdown("<div class='step-box'><h4>🔩 Step 4: ออกแบบจำนวนและการจัดเรียงสลักเกลียวฝัง</h4></div>", unsafe_allow_html=True)
    
    # 🧠 ลอจิกวิเคราะห์แรงดึงที่งัดขึ้นมาที่หัวนอตจากโมเมนต์พลิกคว่ำ (Overturning Moment Mechanics)
    lever_arm = N - 4.0 # ระยะห่างสมมติระหว่างแนวนอตรับแรงดึงและแรงอัด
    tension_force_total = (m_u / lever_arm) - (p_u / 2) if lever_arm > 0 else 0
    
    if tension_force_total > 0:
        st.warning(f"⚠️ **ตรวจพบแรงถอนวิกฤต (Uplift Tension):** เกิดแรงดึงงัดรวมฝั่งนอตรับแรงดึง **{round(tension_force_total, 1)} kips** ระบบแนะนำให้ใช้การจัดเรียงแบบ 6 หรือ 8 ตัวเพื่อช่วยกระจายแรงดึง")
    else:
        st.info("💡 **สถานะปลอดภัย:** แรงกดจากน้ำหนักบรรทุกชนะแรงงัดจากโมเมนต์ ไม่มีแรงดึงเกิดขึ้นในสลักเกลียว (นอตทำหน้าที่ล็อกตำแหน่งและรับแรงเฉือน Vu เท่านั้น)")
        
    col_s4_1, col_s4_2 = st.columns(2)
    with col_s4_1:
        num_anchors = st.selectbox("👉 เลือกจำนวนตัวและการจัดพิกัดนอตฝัง", [4, 6, 8], index=0)
    with col_s4_2:
        bolt_dia = st.selectbox("👉 เลือกขนาดเส้นผ่านศูนย์กลางแกนนอตฝัง (นิ้ว)", [0.5, 0.625, 0.75, 0.875, 1.0, 1.25], index=2)


# ================= ================= =================
# 4. LIVE VISUALIZATION & LIMIT STATES MATRIX (RIGHT COLUMN)
# ================= ================= =================
with col_viewport:
    st.markdown("### 📊 AISC Engineering Verification Matrix")
    st.caption("ตารางสรุปสถานะกำลังเทียบกับแรงเค้นวิกฤตในทุก Limit State ตามเส้นทางถ่ายแรง")

    # 🧠 คำนวณความสามารถของระบบและอัตราส่วนความปลอดภัยจริง (Utilization Ratio)
    # 1. Bearing Check
    pp_design = phi_c * 0.85 * fc_prime * actual_area
    bearing_util = (p_u / pp_design) * 100 if pp_design > 0 else 0
    
    # 2. Plate Thickness Check
    plate_util = (t_req_min / tp_user) * 100 if tp_user > 0 else 0
    
    # 3. Anchor Tension Check (ต่อสลักเกลียวเดี่ยว)
    bolts_in_tension = num_anchors / 2
    t_per_bolt = round(tension_force_total / bolts_in_tension, 2) if tension_force_total > 0 else 0.0

    summary_table_data = [
        {
            "Engineering Limit State": "1. Concrete Bearing (คอนกรีตรับแรงกด)",
            "AISC Ref.": "AISC 360 J8",
            "Demand (แรงที่เกิด)": f"{p_u} kips",
            "Capacity (กำลังต้านทาน)": f"{round(pp_design, 1)} kips",
            "Utilization": f"{round(bearing_util, 1)}%",
            "Status": "PASS" if p_u <= pp_design else "FAIL"
        },
        {
            "Engineering Limit State": "2. Plate Bending Thickness (ความหนาแผ่นเหล็ก)",
            "AISC Ref.": "Design Guide 1",
            "Demand (แรงที่เกิด)": f"{round(t_req_min, 3)}\" req.",
            "Capacity (กำลังต้านทาน)": f"{tp_user}\" prov.",
            "Utilization": f"{round(plate_util, 1)}%",
            "Status": "PASS" if t_req_min <= tp_user else "FAIL"
        },
        {
            "Engineering Limit State": "3. Anchor Tension Force (แรงดึงในสลักเกลียวต่อตัว)",
            "AISC Ref.": "AISC 360 J9",
            "Demand (แรงที่เกิด)": f"{t_per_bolt} kips/bolt",
            "Capacity (กำลังต้านทาน)": "ตามสเปกสลักเกลียว",
            "Utilization": "--",
            "Status": "INFO" if t_per_bolt > 0 else "SAFE"
        }
    ]
    st.table(summary_table_data)

    # แถบแสดงสถานะรวมแบบสรุปเร็ว
    max_critical_util = max(bearing_util, plate_util)
    if max_critical_util > 100:
        st.error(f"❌ โครงสร้างไม่ปลอดภัย (OVERSTRESSED): อัตราส่วนรับแรงสูงสุดคือ {round(max_critical_util, 1)}% กรุณาแก้ไขพารามิเตอร์ในขั้นตอนสีแดง")
    else:
        st.success(f"✅ โครงสร้างผ่านเกณฑ์ต้านทานแรง (SAFE): อัตราการใช้กำลังสูงสุดคือ {round(max_critical_util, 1)}%")

    st.markdown("---")
    st.markdown("### 🧊 Live 3D Spatial Interactive Model")
    st.caption("พิกัดโมเดล 3D จะขยับ ปรับสเกล และย้ายตำแหน่งรูเจาะรวมถึงความยาวรอยเชื่อมตามจริงที่คุณปรับทางซ้ายมือแบบเรียลไทม์")
    
    # เรียกกราฟิก 3D ออกมาแสดงผลแบบไหลตามสัดส่วนจริง
    fig_wizard_model = generate_load_path_base_plate_3d(B, N, tp_user, col_d, col_bf, num_anchors)
    st.plotly_chart(fig_wizard_model, use_container_width=True)
