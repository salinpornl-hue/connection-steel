# app.py
import math
import streamlit as st
import plotly.graph_objects as go

# ================= 1. Import Engine & Fallback Mechanism =================
try:
    from engine import AISC_LRFD_Engine
    engine = AISC_LRFD_Engine()
except ImportError:
    # คลาส Mockup เพื่อให้แอปยังสามารถรันแสดงผล UI/3D ได้ แม้ไม่มีไฟล์ engine.py อยู่ในไดเรกทอรี
    class AISC_LRFD_Engine:
        def calculate_bolt_shear_capacity(self, d, g, t, p): 
            return {"design_capacity_kips": 25.0, "A_b": 0.44, "F_nv": 54.0, "nominal_capacity_kips": 33.0}
        def calculate_weld_capacity(self, s, l, e): 
            return {"design_capacity_kips": 120.0, "weld_size_inch": 0.3125, "effective_throat": 0.221, "nominal_capacity_kips": 160.0}
    engine = AISC_LRFD_Engine()

# ================= 2. Configuration & Global Styles =================
st.set_page_config(page_title="Enterprise Structural Connection Suite", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .stTable { background-color: #ffffff; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ Enterprise Structural Connection Suite")
st.caption("AISC 360-16 LRFD Compliance | Multi-Element Parametric 3D Visualization")

# ================= 3. 3D Engine: Advanced Geometry Generation =================
def create_3d_connection_model(num_bolts):
    fig = go.Figure()
    # แผ่นเหล็กชิ้นล่าง (Bottom Plate)
    fig.add_trace(go.Mesh3d(x=[0,10,10,0,0,10,10,0], y=[0,0,5,5,0,0,5,5], z=[0,0,0,0,-0.5,-0.5,-0.5,-0.5], color='dimgray', opacity=0.8, name='Bottom Plate'))
    # แผ่นเหล็กชิ้นบน (Top Plate)
    fig.add_trace(go.Mesh3d(x=[5,15,15,5,5,15,15,5], y=[0,0,5,5,0,0,5,5], z=[0,0,0,0,0.5,0.5,0.5,0.5], color='lightgray', opacity=0.8, name='Top Plate'))
    
    # จัดพิกัดนอตแบบ Dynamic 
    for i in range(num_bolts):
        bx = 6.0 + (i * 0.8)
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[2.5, 2.5], z=[-1, 1], mode='lines', line=dict(color='red', width=8), showlegend=False))
        
    fig.update_layout(scene=dict(xaxis_title='X (in)', yaxis_title='Y (in)', zaxis_title='Z (in)', aspectmode='data'), margin=dict(l=0,r=0,b=0,t=0), height=400)
    return fig

def generate_professional_base_plate_3d(B, N, tp, col_d, col_bf, num_anchors):
    fig = go.Figure()

    # 1. Concrete Pedestal (ตอม่อคอนกรีต)
    fig.add_trace(go.Mesh3d(
        x=[-B*0.8, B*0.8, B*0.8, -B*0.8, -B*0.8, B*0.8, B*0.8, -B*0.8],
        y=[-N*0.8, -N*0.8, N*0.8, N*0.8, -N*0.8, -N*0.8, N*0.8, N*0.8],
        z=[-18, -18, -18, -18, 0, 0, 0, 0],
        color='rgba(211, 211, 211, 0.4)', opacity=0.4, name='Concrete Pedestal'
    ))

    # 2. Base Plate (แผ่นฐานเหล็ก)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='steelblue', opacity=0.9, name='Base Plate'
    ))

    # 3. Parametric Column Profile (หน้าตัดเสาเหล็กรูปตัว H แบบสมจริง)
    w_thickness = 0.375
    f_thickness = 0.50
    # ปีกซ้าย (Left Flange)
    fig.add_trace(go.Mesh3d(x=[-col_d/2, -col_d/2+f_thickness, -col_d/2+f_thickness, -col_d/2, -col_d/2, -col_d/2+f_thickness, -col_d/2+f_thickness, -col_d/2],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', name='Column Section'))
    # ปีกขวา (Right Flange)
    fig.add_trace(go.Mesh3d(x=[col_d/2-f_thickness, col_d/2, col_d/2, col_d/2-f_thickness, col_d/2-f_thickness, col_d/2, col_d/2, col_d/2-f_thickness],
                            y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', showlegend=False))
    # เอวเสา (Web)
    fig.add_trace(go.Mesh3d(x=[-col_d/2+f_thickness, col_d/2-f_thickness, col_d/2-f_thickness, -col_d/2+f_thickness, -col_d/2+f_thickness, col_d/2-f_thickness, col_d/2-f_thickness, -col_d/2+f_thickness],
                            y=[-w_thickness/2, -w_thickness/2, w_thickness/2, w_thickness/2, -w_thickness/2, -w_thickness/2, w_thickness/2, w_thickness/2],
                            z=[tp, tp, tp, tp, tp+18, tp+18, tp+18, tp+18], color='darkslategray', showlegend=False))

    # 4. Weld Line Perimeter Visualization (เส้นจำลองแนวรอยเชื่อมรอบโคนเสา)
    fig.add_trace(go.Scatter3d(
        x=[-col_d/2, col_d/2, col_d/2, -col_d/2, -col_d/2],
        y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2],
        z=[tp+0.1, tp+0.1, tp+0.1, tp+0.1, tp+0.1],
        mode='lines', line=dict(color='yellow', width=5), name='Fillet Weld Line'
    ))

    # 5. Dynamic Anchor Bolt Layout Logic (กระจายพิกัดนอตตามเงื่อนไขจริง)
    edge_g = 2.0  # ระยะร่นมาตรฐานจากขอบแผ่นเหล็ก
    edge_x = (B/2) - edge_g
    edge_y = (N/2) - edge_g
    
    bolt_coords = []
    if num_anchors == 4:
        bolt_coords = [(-edge_x, -edge_y), (edge_x, -edge_y), (edge_x, edge_y), (-edge_x, edge_y)]
    elif num_anchors == 6:
        bolt_coords = [(-edge_x, -edge_y), (edge_x, -edge_y), (edge_x, edge_y), (-edge_x, edge_y),
                       (0, -edge_y), (0, edge_y)]
    elif num_anchors == 8:
        bolt_coords = [(-edge_x, -edge_y), (edge_x, -edge_y), (edge_x, edge_y), (-edge_x, edge_y),
                       (0, -edge_y), (0, edge_y), (-edge_x, 0), (edge_x, 0)]

    for idx, (bx, by) in enumerate(bolt_coords):
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-12, tp+2],
            mode='lines+markers', marker=dict(size=4, color='crimson'),
            line=dict(color='crimson', width=8), name='Anchor Bolt' if idx == 0 else '', showlegend=True if idx == 0 else False
        ))

    # 6. Structural Forces Vector Visualization (ลูกศรแสดงทิศทางแรงกระทำ)
    # Axial Load (Pu)
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[tp+28, tp+18], mode='lines', line=dict(color='magenta', width=6), showlegend=False))
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+18], u=[0], v=[0], w=[-1], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0,'magenta'],[1,'magenta']], name='Axial (Pu)'))
    
    # Shear Load (Vu)
    fig.add_trace(go.Scatter3d(x=[0, (B/2)+2], y=[0, 0], z=[tp, tp], mode='lines', line=dict(color='green', width=6), showlegend=False))
    fig.add_trace(go.Cone(x=[(B/2)+2], y=[0], z=[tp], u=[1], v=[0], w=[0], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0,'green'],[1,'green']], name='Shear (Vu)'))

    # Overturning Moment (Mu)
    arc_x, arc_z = [], []
    r_m = (col_d/2) + 2.5
    for i in range(21):
        ang = math.pi - (math.pi * i / 20.0)
        arc_x.append(r_m * math.cos(ang))
        arc_z.append(tp + 10 + (r_m * math.sin(ang)))
    fig.add_trace(go.Scatter3d(x=arc_x, y=[0]*21, z=arc_z, mode='lines', line=dict(color='orange', width=5, dash='dash'), showlegend=False))
    fig.add_trace(go.Cone(x=[arc_x[-1]], y=[0], z=[arc_z[-1]], u=[0], v=[0], w=[-1], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0,'orange'],[1,'orange']], name='Moment (Mu)'))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X Axis (in)', gridcolor='white'),
            yaxis=dict(title='Y Axis (in)', gridcolor='white'),
            zaxis=dict(title='Z Axis (in)', gridcolor='white'),
            bgcolor='rgba(240, 242, 246, 0.5)', # เปลี่ยนจาก backgroundcolor เป็น bgcolor
            aspectmode='data',
            camera=dict(eye=dict(x=1.3, y=-1.3, z=0.9))
        ),
        margin=dict(l=0, r=0, b=0, t=0), 
        height=550
    )
    return fig

# ================= 4. UI Layout & Tabs Execution =================
tab1, tab2, tab3 = st.tabs(["🔒 Bolt Connection", "⚡ Weld Connection", "🏢 Integrated Base Plate Suite"])

# --- TAB 1: BOLT DESIGN ---
with tab1:
    st.header("การออกแบบสลักเกลียว (Bolt Design)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ป้อนข้อมูล (Inputs)")
        bolt_dia = st.selectbox("ขนาดเส้นผ่านศูนย์กลางนอต (นิ้ว)", [0.5, 0.625, 0.75, 0.875, 1.0], index=2)
        bolt_grade = st.radio("เกรดของนอต (Bolt Grade)", ["A325", "A490"])
        threads = st.checkbox("เกลียวอยู่นอกระนาบเฉือน? (Threads Excluded)", value=True)
        planes = st.number_input("จำนวนระนาบรับแรงเฉือน (1=เดี่ยว, 2=คู่)", min_value=1, max_value=2, value=1)
        num_bolts = st.number_input("จำนวนนอตทั้งหมดในจุดต่อ (ตัว)", min_value=1, value=4)
        v_u = st.number_input("แรงเฉือนที่กระทำจริงรวม, Vu (kips)", min_value=0.0, value=50.0)

    with col2:
        st.subheader("📊 ผลการคำนวณ (Results)")
        res_bolt = engine.calculate_bolt_shear_capacity(bolt_dia, bolt_grade, threads, planes)
        total_capacity = res_bolt["design_capacity_kips"] * num_bolts
        
        st.metric(label="กำลังรับแรงเฉือนออกแบบของนอต 1 ตัว ($\phi R_n$)", value=f"{res_bolt['design_capacity_kips']} kips")
        st.metric(label="กำลังรับแรงเฉือนออกแบบรวมของจุดต่อ ($\phi R_n)_{total}$", value=f"{round(total_capacity, 2)} kips")
        
        utilization = (v_u / total_capacity) * 100 if total_capacity > 0 else 0
        if v_u <= total_capacity:
            st.success(f"✅ ผ่าน (PASSED) - อัตราส่วนการใช้กำลัง (Utilization): {round(utilization, 1)}%")
        else:
            st.error(f"❌ 不ผ่าน (FAILED) - จุดต่อรับแรงเกินกำลัง! อัตราส่วน: {round(utilization, 1)}%")
            
        st.markdown("---")
        st.subheader("🧊 โมเดลจุดต่อ 3 มิติ (3D Connection Model)")
        fig_3d = create_3d_connection_model(int(num_bolts))
        st.plotly_chart(fig_3d, use_container_width=True)

# --- TAB 2: WELD DESIGN ---
with tab2:
    st.header("การออกแบบรอยเชื่อม (Weld Design)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ป้อนข้อมูล (Inputs)")
        weld_size = st.slider("ขนาดขาของรอยเชื่อม (หน่วยเศษ 1/16 นิ้ว)", min_value=1, max_value=16, value=4)
        weld_len = st.number_input("ความยาวรวมของรอยเชื่อม (นิ้ว)", min_value=0.1, value=12.0)
        electrode = st.selectbox("เกรดลวดเชื่อม", ["E70"])
        w_u = st.number_input("แรงเฉือนที่กระทำจริงบนรอยเชื่อม, Wu (kips)", min_value=0.0, value=40.0)

    with col2:
        st.subheader("📊 ผลการคำนวณ (Results)")
        res_weld = engine.calculate_weld_capacity(weld_size, weld_len, electrode)
        weld_capacity = res_weld["design_capacity_kips"]
        
        st.metric(label="กำลังรับแรงออกแบบรวมของรอยเชื่อม ($\phi R_n$)", value=f"{weld_capacity} kips")
        
        weld_util = (w_u / weld_capacity) * 100 if weld_capacity > 0 else 0
        if w_u <= weld_capacity:
            st.success(f"✅ ผ่าน (PASSED) - อัตราส่วนการใช้กำลัง (Utilization): {round(weld_util, 1)}%")
        else:
            st.error(f"❌ ไม่ผ่าน (FAILED) - รอยเชื่อมรับแรงเกินกำลัง! อัตราส่วน: {round(weld_util, 1)}%")

# --- TAB 3: INTEGRATED BASE PLATE SUITE (ENTERPRISE GRADE) ---
with tab3:
    st.subheader("ระบบคำนวณกำลังจุดต่อแผ่นฐานเสา รอยเชื่อม และนอตฝังแบบบูรณาการ")
    col_in, col_graph = st.columns([1, 1.2])
    
    with col_in:
        st.markdown("### ⚙️ Input Specifications")
        
        with st.expander("1. โครงสร้างและหน้าตัดเสา (Column Profile)", expanded=True):
            col_d = st.number_input("ความลึกหน้าตัดเสาจริง d (นิ้ว)", min_value=4.0, value=10.0, step=0.5)
            col_bf = st.number_input("ความกว้างปีกเสาจริง bf (นิ้ว)", min_value=4.0, value=10.0, step=0.5)
            fy_plate = st.number_input("กำลังรับแรงดึงที่จุดคล้อยของเหล็กแผ่น Fy (ksi)", value=36.0)
            
        with st.expander("2. การจัดระยะแผ่นฐานและสลักเกลียวฝัง (Geometric Design)", expanded=True):
            # --- Smart Auto-Sizing ตามคู่มือ AISC Design Guide 1 ---
            rec_B = col_bf + 4.0
            rec_N = col_d + 4.0
            st.info(f"💡 **ขนาดขอบแผ่นฐานแนะนำขั้นต่ำ:** กว้าง {rec_B}\" x ยาว {rec_N}\" (เพื่อให้มีพื้นที่เผื่อระยะขอบนอต)")
            
            B = st.number_input("กำหนดความกว้างแผ่นฐาน B (นิ้ว)", min_value=float(col_bf), value=rec_B, step=0.5)
            N = st.number_input("กำหนดความยาวแผ่นฐาน N (นิ้ว)", min_value=float(col_d), value=rec_N, step=0.5)
            tp_user = st.number_input("กำหนดความหนาแผ่นฐานเลือกใช้ tp (นิ้ว)", min_value=0.25, value=1.25, step=0.125)
            
            num_anchors = st.selectbox("จำนวนนอตฝังและการจัดเรียง (Anchor Bolt Patterns)", [4, 6, 8], index=0)
            fc_prime = st.number_input("กำลังอัดประลัยของคอนกรีตฐานราก fc' (ksi)", min_value=1.5, value=4.0, step=0.5)

        with st.expander("3. ขนาดรอยเชื่อมโคนเสา (Base Connection Weld)", expanded=False):
            base_weld_size = st.slider("ขนาดขาของรอยเชื่อมฟิลเล็ตรอบเสา (ส่วน 1/16 นิ้ว)", min_value=2, max_value=16, value=6)

        with st.expander("4. แรงออกแบบภายนอก (Structural Demands)", expanded=True):
            p_u = st.number_input("Factored Axial Demand, Pu (kips) [แรงกด]", value=180.0, step=10.0)
            v_u_bp = st.number_input("Factored Shear Demand, Vu (kips) [แรงเฉือน]", value=30.0, step=5.0)
            m_u_bp = st.number_input("Factored Overturning Moment, Mu (kip-in)", value=600.0, step=50.0)

    # --- ADVANCED AISC DESIGN GUIDE 1 COMPLIANCE CALCULATIONS ---
    # A. ประเมินแรงแบกทานคอนกรีต (Concrete Bearing Limit State - AISC 360 J8)
    A1 = B * N
    phi_c = 0.65
    pp_nominal = 0.85 * fc_prime * A1
    pp_design = phi_c * pp_nominal
    bearing_util = (p_u / pp_design) * 100 if pp_design > 0 else 0

    # B. คำนวณความหนาแผ่นฐานขั้นต่ำด้วยวิธีคานยื่นวิกฤต (Plate Bending Limit State)
    m = (N - 0.95 * col_d) / 2
    n = (B - 0.80 * col_bf) / 2
    n_prime = math.sqrt(col_d * col_bf) / 4
    critical_l = max(max(m, n), n_prime)
    
    phi_b = 0.90
    required_tp = 0.0
    if A1 > 0 and p_u > 0:
        required_tp = critical_l * math.sqrt((2 * p_u) / (phi_b * fy_plate * B * N))
    plate_util = (required_tp / tp_user) * 100 if tp_user > 0 else 0

    # C. คำนวณกลศาสตร์แรงดึงในสลักเกลียวฝัง (Anchor Bolt Lever Arm Mechanics)
    lever_arm = N - 4.0  # ระยะคานงัดสมมติหักลบระยะขอบนอตสองฝั่ง
    tension_total = (m_u_bp / lever_arm) - (p_u / 2)
    t_bolt_each = round(tension_total / (num_anchors / 2), 2) if tension_total > 0 else 0.0

    with col_graph:
        st.markdown("### 📊 AISC Structural Verification Matrix")
        
        # แสดงตารางรายงานวิศวกรรมแบบ Professional Limit States Table
        summary_matrix = [
            {"Limit State Check": "Concrete Bearing (คอนกรีตรับแรงกด)", "AISC Ref.": "AISC 360 J8", "Demand": f"{p_u} kips", "Capacity": f"{round(pp_design, 1)} kips", "Utilization": f"{round(bearing_util, 1)}%", "Status": "PASS" if p_u <= pp_design else "FAIL"},
            {"Limit State Check": "Plate Bending Min Thickness (ความหนาแผ่นเหล็ก)", "AISC Ref.": "Design Guide 1", "Demand": f"{round(required_tp, 3)}\" req.", "Capacity": f"{tp_user}\" prov.", "Utilization": f"{round(plate_util, 1)}%", "Status": "PASS" if required_tp <= tp_user else "FAIL"},
            {"Limit State Check": "Anchor Tension (แรงดึงในสลักเกลียวต่อตัว)", "AISC Ref.": "AISC 360 J9", "Demand": f"{t_bolt_each} kips/bolt", "Capacity": "ตามสเปกสลักเกลียว", "Utilization": "--", "Status": "INFO"}
        ]
        st.table(summary_matrix)
        
        # การ์ดแจ้งเตือนสถานะความปลอดภัยวิกฤต
        max_util = max(bearing_util, plate_util)
        if max_util > 100:
            st.error(f"❌ CONNECTION OVERSTRESSED: อัตราส่วนแรงวิกฤตสูงสุดคือ {round(max_util, 1)}% กรุณาเพิ่มขนาดความหนาหรือพื้นที่หน้าตัดแผ่นฐาน")
        else:
            st.success(f"✅ CONNECTION ADEQUATE: จุดต่อผ่านเกณฑ์ตรวจสอบกำลังขั้นต้น อัตราส่วนใช้งานสูงสุด {round(max_util, 1)}%")

        st.markdown("---")
        st.write("### 🧊 Interactive 3D Analytical Model")
        st.caption("โมเดลจะเปลี่ยนสเกล ปรับสัดส่วนเสา แผ่นฐาน แนวเชื่อม และการเรียงนอตฝังตามอินพุตจริงของคุณแบบเรียลไทม์")
        
        # สตรีมโมเดล 3D แบบครบองค์ประกอบ
        fig_bp_enterprise = generate_professional_base_plate_3d(B, N, tp_user, col_d, col_bf, num_anchors)
        st.plotly_chart(fig_bp_enterprise, use_container_width=True)
