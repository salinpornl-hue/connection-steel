# app.py
import streamlit as st
from engine import AISC_LRFD_Engine

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Steel Connection Design (AISC 360)", layout="wide")
st.title("🔩 Steel Connection Design Tool (AISC 360-16 LRFD)")
st.write("พัฒนาโดย Senior Engineer - โปรแกรมคำนวณกำลังจุดต่อโครงสร้างเหล็ก")

# เรียกใช้งาน Engine
engine = AISC_LRFD_Engine()

# แบ่งหน้าจอเป็น 2 แท็บ: แท็บคำนวณนอต และแท็บคำนวณรอยเชื่อม
tab1, tab2 = st.tabs(["Bolt Connection", "Weld Connection"])

# ================= TAB 1: BOLT DESIGN =================
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
            
        # รายละเอียดการคำนวณย่อย
        with st.expander("🔍 ดูรายการคำนวณแบบละเอียด (Calculation Report)"):
            st.write(f"- พื้นฐานหน้าตัดนอต ($A_b$): {res_bolt['A_b']} $in^2$")
            st.write(f"- หน่วยแรงเฉือนที่กำหนด ($F_{{nv}}$): {res_bolt['F_nv']} ksi")
            st.write(f"- กำลังรับแรงเฉือนระบุ ($R_n$ ต่อตัว): {res_bolt['nominal_capacity_kips']} kips")
            st.write(f"- ค่าตัวคูณลดกำลัง ($\phi$): 0.75")

# ================= TAB 2: WELD DESIGN =================
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
