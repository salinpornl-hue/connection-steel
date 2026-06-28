# app.py
import streamlit as st
import plotly.graph_objects as go
from engine import AISC_LRFD_Engine

# ================= 1. ตั้งค่าหน้าเว็บ Streamlit =================
st.set_page_config(page_title="Steel Connection Design (AISC 360)", layout="wide")
st.title("🔩 Steel Connection Design Tool (AISC 360-16 LRFD)")
st.write("พัฒนาโดย Senior Engineer - โปรแกรมคำนวณกำลังจุดต่อโครงสร้างเหล็ก")

# ================= 2. ฟังก์ชันสร้าง 3D Model =================
def create_3d_connection_model(num_bolts):
    fig = go.Figure()

    # วาดแผ่นเหล็กชิ้นล่าง (Bottom Plate) - สีเทาเข้ม
    fig.add_trace(go.Mesh3d(
        x=[0, 10, 10, 0, 0, 10, 10, 0],
        y=[0, 0, 5, 5, 0, 0, 5, 5],
        z=[0, 0, 0, 0, -0.5, -0.5, -0.5, -0.5],
        color='dimgray',
        opacity=0.8,
        name='Bottom Plate'
    ))

    # วาดแผ่นเหล็กชิ้นบน (Top Plate) - สีเทาอ่อน
    fig.add_trace(go.Mesh3d(
        x=[5, 15, 15, 5, 5, 15, 15, 5],
        y=[0, 0, 5, 5, 0, 0, 5, 5],
        z=[0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5],
        color='lightgray',
        opacity=0.8,
        name='Top Plate'
    ))

    # วาดนอต (Bolts) ตามจำนวนที่เลือก (จำลองตำแหน่งบนพื้นที่ทับซ้อน X: 5 ถึง 10)
    bolt_x = []
    bolt_y = []
    
    # จัดเรียงตำแหน่งนอตแบบง่ายๆ
    if num_bolts == 2:
        bolt_x, bolt_y = [7.5, 7.5], [1.5, 3.5]
    elif num_bolts == 4:
        bolt_x, bolt_y = [6.5, 8.5, 6.5, 8.5], [1.5, 1.5, 3.5, 3.5]
    elif num_bolts == 6:
        bolt_x, bolt_y = [6.0, 7.5, 9.0, 6.0, 7.5, 9.0], [1.5, 1.5, 1.5, 3.5, 3.5, 3.5]
    else:
        # ถ้าเป็นเลขอื่น ให้วางตำแหน่งตรงกลางสมมติไปก่อน
        bolt_x = [7.5] * num_bolts
        bolt_y = [2.5] * num_bolts

    # สร้างแท่งทรงกระบอกจำลองนอต (เส้นหนาสีแดง)
    for bx, by in zip(bolt_x, bolt_y):
        fig.add_trace(go.Scatter3d(
            x=[bx, bx], y=[by, by], z=[-1, 1],
            mode='lines',
            line=dict(color='red', width=10),
            name='Bolt'
        ))

    # ปรับมุมมองกล้อง 3D
    fig.update_layout(
        scene=dict(
            xaxis_title='X (in)',
            yaxis_title='Y (in)',
            zaxis_title='Z (in)',
            aspectmode='data' # ทำให้สเกล X, Y, Z สมส่วนกันจริง
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=400
    )
    return fig
import math
import plotly.graph_objects as go

def create_3d_base_plate_model(B, N, tp, col_d, col_bf):
    fig = go.Figure()

    # 1. Concrete Pedestal (ตอม่อคอนกรีต)
    fig.add_trace(go.Mesh3d(
        x=[-B, B, B, -B, -B, B, B, -B],
        y=[-N, -N, N, N, -N, -N, N, N],
        z=[-15, -15, -15, -15, 0, 0, 0, 0],
        color='lightgray', opacity=0.4, name='Concrete Pedestal'
    ))

    # 2. Base Plate (แผ่นฐานเหล็ก)
    fig.add_trace(go.Mesh3d(
        x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
        y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2],
        z=[0, 0, 0, 0, tp, tp, tp, tp],
        color='steelblue', opacity=1.0, name='Base Plate'
    ))

    # 3. Column (เสาเหล็กจำลองรูปตัว H/I)
    # ปีกเสา (Flanges)
    fig.add_trace(go.Mesh3d(
        x=[-col_d/2, -col_d/2+0.5, -col_d/2+0.5, -col_d/2, -col_d/2, -col_d/2+0.5, -col_d/2+0.5, -col_d/2],
        y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
        z=[tp, tp, tp, tp, tp+15, tp+15, tp+15, tp+15],
        color='dimgray', name='Column Flange'
    ))
    fig.add_trace(go.Mesh3d(
        x=[col_d/2-0.5, col_d/2, col_d/2, col_d/2-0.5, col_d/2-0.5, col_d/2, col_d/2, col_d/2-0.5],
        y=[-col_bf/2, -col_bf/2, col_bf/2, col_bf/2, -col_bf/2, -col_bf/2, col_bf/2, col_bf/2],
        z=[tp, tp, tp, tp, tp+15, tp+15, tp+15, tp+15],
        color='dimgray', name='Column Flange'
    ))
    # เอวเสา (Web)
    fig.add_trace(go.Mesh3d(
        x=[-col_d/2+0.5, col_d/2-0.5, col_d/2-0.5, -col_d/2+0.5, -col_d/2+0.5, col_d/2-0.5, col_d/2-0.5, -col_d/2+0.5],
        y=[-0.25, -0.25, 0.25, 0.25, -0.25, -0.25, 0.25, 0.25],
        z=[tp, tp, tp, tp, tp+15, tp+15, tp+15, tp+15],
        color='dimgray', name='Column Web'
    ))

    # 4. Anchor Bolts (นอตฝัง 4 มุม)
    bolt_dist_x = (B/2) - 2.0 
    bolt_dist_y = (N/2) - 2.0
    for bx in [-bolt_dist_x, bolt_dist_x]:
        for by in [-bolt_dist_y, bolt_dist_y]:
            fig.add_trace(go.Scatter3d(
                x=[bx, bx], y=[by, by], z=[-10, tp+2],
                mode='lines', line=dict(color='red', width=8), name='Anchor Bolt'
            ))

    # ================= 5. เพิ่มการแสดงผลแรง (FORCE VECTORS) ให้ชัดเจน =================
    
    # 5.1 Axial Force (Pu) - ลูกศรพุ่งลงตรงกลางเสา
    # เส้นก้านลูกศร
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[tp+25, tp+12], mode='lines', line=dict(color='magenta', width=6), name='Pu Shaft', showlegend=False))
    # หัวลูกศร (Cone) ชี้ลง z=-1
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+12], u=[0], v=[0], w=[-1], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0, 'magenta'], [1, 'magenta']], name='Pu Head'))
    # Label
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[tp+28], mode='text', text=['↓ Pu (Axial)'], textfont=dict(color='magenta', size=14), showlegend=False))

    # 5.2 Shear Force (Vu) - ลูกศรไถลไปตามแกน X ที่ระดับรอยต่อ (Z = tp)
    # เส้นก้านลูกศร
    fig.add_trace(go.Scatter3d(x=[0, (B/2)+2], y=[0, 0], z=[tp, tp], mode='lines', line=dict(color='green', width=6), name='Vu Shaft', showlegend=False))
    # หัวลูกศร (Cone) ชี้ไปทาง x=1
    fig.add_trace(go.Cone(x=[(B/2)+2], y=[0], z=[tp], u=[1], v=[0], w=[0], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0, 'green'], [1, 'green']], name='Vu Head'))
    # Label
    fig.add_trace(go.Scatter3d(x=[(B/2)+5], y=[0], z=[tp], mode='text', text=['→ Vu (Shear)'], textfont=dict(color='green', size=14), showlegend=False))

    # 5.3 Overturning Moment (Mu) - สร้างเส้นโค้งงัดข้ามหัวเสา
    arc_x, arc_y, arc_z = [], [], []
    r_moment = (col_d/2) + 3 # รัศมีวงโค้งของโมเมนต์
    # สร้างจุดโค้ง 180 องศา จากซ้ายไปขวา
    for i in range(21):
        angle = math.pi - (math.pi * i / 20.0) 
        arc_x.append(r_moment * math.cos(angle))
        arc_y.append(0)
        arc_z.append(tp + 8 + (r_moment * math.sin(angle)))
        
    # เส้นโค้ง
    fig.add_trace(go.Scatter3d(x=arc_x, y=arc_y, z=arc_z, mode='lines', line=dict(color='orange', width=5, dash='dash'), name='Mu Arc', showlegend=False))
    # หัวลูกศรของโมเมนต์ ชี้ลงที่ปลายเส้นโค้งฝั่งขวา
    fig.add_trace(go.Cone(x=[arc_x[-1]], y=[0], z=[arc_z[-1]], u=[0], v=[0], w=[-1], sizemode="absolute", sizeref=3, showscale=False, colorscale=[[0, 'orange'], [1, 'orange']], name='Mu Head'))
    # Label
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[tp + 8 + r_moment + 3], mode='text', text=['↻ Mu (Moment)'], textfont=dict(color='orange', size=14), showlegend=False))

    # ==============================================================================

    # ปรับแต่งมุมกล้องและ Layout
    fig.update_layout(
        scene=dict(
            xaxis_title='X (in)', yaxis_title='Y (in)', zaxis_title='Z (in)', 
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=1.0) # หมุนกล้องเริ่มต้นให้เห็นภาพ 3 มิติชัดๆ
            )
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=550
    )
    return fig


# ================= 3. เรียกใช้งาน Engine & UI =================
engine = AISC_LRFD_Engine()

# แบ่งหน้าจอเป็น 2 แท็บ: แท็บคำนวณนอต และแท็บคำนวณรอยเชื่อม
tab1, tab2, tab3 = st.tabs(["Bolt Connection", "Weld Connection", "Base Plate"])

# ----------------- TAB 1: BOLT DESIGN -----------------
with tab1:
    st.header("การออกแบบสลักเกลียว (Bolt Design)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ป้อนข้อมูล (Inputs)")
        bolt_dia = st.selectbox("ขนาดเส้นผ่านศูนย์กลางนอต (นิ้ว)", [0.5, 0.625, 0.75, 0.875, 1.0], index=2)
        bolt_grade = st.radio("เกรดของนอต (Bolt Grade)", ["A325", "A490"])
        threads = st.checkbox("เกลียวอยู่นอกระนาบเฉือน? (Threads Excluded จากระนาบตัด)", value=True)
        planes = st.number_input("จำนวนระนาบรับแรงเฉือน (1=เดี่ยว, 2=คู่)", min_value=1, max_value=2, value=1)
        num_bolts = st.number_input("จำนวนนอตทั้งหมดในจุดต่อ (ตัว)", min_value=1, value=4)
        
        # แรงที่กระทำจริง (Factored Load)
        v_u = st.number_input("แรงเฉือนที่กระทำจริงรวม, Vu (kips)", min_value=0.0, value=50.0)

    with col2:
        st.subheader("📊 ผลการคำนวณ (Results)")
        # คำนวณกำลังของนอต 1 ตัว
        res_bolt = engine.calculate_bolt_shear_capacity(bolt_dia, bolt_grade, threads, planes)
        
        # คำนวณกำลังรวมของจุดต่อ (Total Capacity)
        total_capacity = res_bolt["design_capacity_kips"] * num_bolts
        
        # แสดงผลลัพธ์หลัก
        st.metric(label="กำลังรับแรงเฉือนออกแบบของนอต 1 ตัว ($\phi R_n$)", value=f"{res_bolt['design_capacity_kips']} kips")
        st.metric(label="กำลังรับแรงเฉือนออกแบบรวมของจุดต่อ ($\phi R_n)_{total}$", value=f"{round(total_capacity, 2)} kips")
        
        # ตรวจสอบความปลอดภัย (Check Capacity)
        utilization = (v_u / total_capacity) * 100 if total_capacity > 0 else 0
        
        if v_u <= total_capacity:
            st.success(f"✅ ผ่าน (PASSED) - อัตราส่วนการใช้กำลัง (Utilization): {round(utilization, 1)}%")
        else:
            st.error(f"❌ ไม่ผ่าน (FAILED) - จุดต่อรับแรงเกินกำลัง! อัตราส่วน: {round(utilization, 1)}%")
            
        # แสดงโมเดล 3D
        st.markdown("---")
        st.subheader("🧊 โมเดลจุดต่อ 3 มิติ (3D Connection Model)")
        fig_3d = create_3d_connection_model(int(num_bolts))
        st.plotly_chart(fig_3d, use_container_width=True)
            
        # รายละเอียดการคำนวณย่อย
        with st.expander("🔍 ดูรายการคำนวณแบบละเอียด (Calculation Report)"):
            st.write(f"- พื้นฐานหน้าตัดนอต ($A_b$): {res_bolt['A_b']} $in^2$")
            st.write(f"- หน่วยแรงเฉือนที่กำหนด ($F_{{nv}}$): {res_bolt['F_nv']} ksi")
            st.write(f"- กำลังรับแรงเฉือนระบุ ($R_n$ ต่อตัว): {res_bolt['nominal_capacity_kips']} kips")
            st.write(f"- ค่าตัวคูณลดกำลัง ($\phi$): 0.75")

# ----------------- TAB 2: WELD DESIGN -----------------
with tab2:
    st.header("การออกแบบรอยเชื่อม (Weld Design)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ป้อนข้อมูล (Inputs)")
        weld_size = st.slider("ขนาดขาของรอยเชื่อม (หน่วยเศษ 1/16 นิ้ว)", min_value=1, max_value=16, value=4)
        weld_len = st.number_input("ความยาวรวมของรอยเชื่อม (นิ้ว)", min_value=0.1, value=12.0)
        electrode = st.selectbox("เกรดลวดเชื่อม", ["E70"])
        
        # แรงที่กระทำจริง (Factored Load)
        w_u = st.number_input("แรงเฉือนที่กระทำจริงบนรอยเชื่อม, Wu (kips)", min_value=0.0, value=40.0)

    with col2:
        st.subheader("📊 ผลการคำนวณ (Results)")
        res_weld = engine.calculate_weld_capacity(weld_size, weld_len, electrode)
        
        weld_capacity = res_weld["design_capacity_kips"]
        
        st.metric(label="กำลังรับแรงออกแบบรวมของรอยเชื่อม ($\phi R_n$)", value=f"{weld_capacity} kips")
        
        # ตรวจสอบความปลอดภัย
        weld_util = (w_u / weld_capacity) * 100 if weld_capacity > 0 else 0
        
        if w_u <= weld_capacity:
            st.success(f"✅ ผ่าน (PASSED) - อัตราส่วนการใช้กำลัง (Utilization): {round(weld_util, 1)}%")
        else:
            st.error(f"❌ ไม่ผ่าน (FAILED) - รอยเชื่อมรับแรงเกินกำลัง! อัตราส่วน: {round(weld_util, 1)}%")
            
        with st.expander("🔍 ดูรายการคำนวณแบบละเอียด (Calculation Report)"):
            st.write(f"- ขนาดรอยเชื่อมจริง: {res_weld['weld_size_inch']} นิ้ว")
            st.write(f"- ความหนาประสิทธิผล ($t_e$): {res_weld['effective_throat']} นิ้ว")
            st.write(f"- หน่วยแรงรอยเชื่อมระบุ ($F_{{nw}}$): 42.0 ksi (0.60 * 70 ksi)")
            st.write(f"- กำลังระบุของรอยเชื่อม ($R_n$): {res_weld['nominal_capacity_kips']} kips")







# ================= TAB 3: BASE PLATE DESIGN =================
with tab3:
    st.header("การออกแบบแผ่นฐานเสาและตอม่อ (Base Plate & Pedestal)")
    
    col1, col2 = st.columns([1, 1.2]) # ให้คอลัมน์ขวากว้างกว่านิดหน่อยเพื่อแสดง 3D
    
    with col1:
        st.subheader("📥 ป้อนข้อมูล (Inputs)")
        st.markdown("**ขนาดแผ่นฐาน (Base Plate)**")
        B = st.number_input("ความกว้างแผ่นฐาน B (นิ้ว) ขนานแกน X", min_value=6.0, value=14.0)
        N = st.number_input("ความยาวแผ่นฐาน N (นิ้ว) ขนานแกน Y", min_value=6.0, value=14.0)
        tp = st.number_input("ความหนาแผ่นฐาน tp (นิ้ว)", min_value=0.25, value=1.0)
        
        st.markdown("**ข้อมูลวัสดุ**")
        fc_prime = st.number_input("กำลังอัดคอนกรีต fc' (ksi) [เช่น 280 ksc ≈ 4.0 ksi]", min_value=1.0, value=4.0)
        
        st.markdown("**แรงที่กระทำ (Factored Loads)**")
        p_u = st.number_input("แรงตามแนวแกน, Pu (kips) [แรงกด+]", min_value=0.0, value=150.0)
        v_u_bp = st.number_input("แรงเฉือน, Vu (kips)", min_value=0.0, value=25.0)
        m_u_bp = st.number_input("โมเมนต์ดัด, Mu (kip-in)", min_value=0.0, value=500.0)

    with col2:
        st.subheader("📊 ผลการคำนวณและโมเดล (Results & 3D)")
        
        # คำนวณ
        res_bp = engine.calculate_base_plate_bearing(B, N, fc_prime)
        bp_capacity = res_bp["design_capacity_kips"]
        
        st.metric(label="กำลังรับแรงแบกทานของคอนกรีต ($\phi_c P_p$)", value=f"{bp_capacity} kips")
        
        # ตรวจสอบเฉพาะแรงกดตามแนวแกนเบื้องต้น (Axial only simplified)
        bp_util = (p_u / bp_capacity) * 100 if bp_capacity > 0 else 0
        if p_u <= bp_capacity:
            st.success(f"✅ ผ่าน (PASSED) - อัตราส่วนรับแรงกดทับ: {round(bp_util, 1)}%")
        else:
            st.error(f"❌ ไม่ผ่าน (FAILED) - คอนกรีตรับแรงกดไม่ไหว! อัตราส่วน: {round(bp_util, 1)}%")
            
        # แสดงโมเดล 3D แบบเห็นทุก Element และ Force
        st.markdown("---")
        st.write("🧊 **3D Element Analysis Model** (แสดงตำแหน่งเสา, แผ่นฐาน, นอตฝัง และทิศทางแรง)")
        # สมมติขนาดหน้าตัดเสา H-beam (Depth=8, Flange Width=8) สำหรับวาดโมเดล
        fig_bp_3d = create_3d_base_plate_model(B, N, tp, col_d=8.0, col_bf=8.0)
        st.plotly_chart(fig_bp_3d, use_container_width=True)
