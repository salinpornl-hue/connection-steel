# app.py
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. PROFESSIONAL DATABASE & METRIC SPEC
# ==========================================
THAI_H_BEAM_PROFILES = {
    "H 200x200x8x12": {"d": 200.0, "bf": 200.0, "tw": 8.0, "tf": 12.0, "weight": 49.9},
    "H 250x250x9x14": {"d": 250.0, "bf": 250.0, "tw": 9.0, "tf": 14.0, "weight": 72.4},
    "H 300x300x10x15": {"d": 300.0, "bf": 300.0, "tw": 10.0, "tf": 15.0, "weight": 94.0},
    "H 350x350x12x19": {"d": 350.0, "bf": 350.0, "tw": 12.0, "tf": 19.0, "weight": 137.0},
    "H 400x400x13x21": {"d": 400.0, "bf": 400.0, "tw": 13.0, "tf": 21.0, "weight": 172.0}
}

THAI_PLATE_THICKNESSES = [12, 16, 19, 22, 25, 28, 32, 38, 50]

THAI_ANCHOR_BOLTS = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area": 157.0, "F_nt": 300.0, "F_nv": 180.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area": 245.0, "F_nt": 300.0, "F_nv": 180.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area": 353.0, "F_nt": 300.0, "F_nv": 180.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area": 561.0, "F_nt": 600.0, "F_nv": 360.0},
    "M36 (Grade 8.8)": {"dia": 36.0, "area": 817.0, "F_nt": 600.0, "F_nv": 360.0}
}

st.set_page_config(page_title="AISC Senior Structural Connection Engine", layout="wide")

# CSS Styling
st.markdown("""
    <style>
    .report-title { font-size: 1.6rem; font-weight: bold; color: #1e293b; margin-top: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
    .step-header { background-color: #0f172a; color: white; padding: 10px 15px; border-radius: 6px; margin-top: 15px; font-weight: bold; border-left: 5px solid #3b82f6; }
    .rec-box { background-color: #f0fdf4; color: #166534; padding: 12px; border-radius: 6px; border: 1px solid #bbf7d0; margin-top: 8px; font-weight: 500; }
    .danger-box { background-color: #fef2f2; color: #991b1b; padding: 12px; border-radius: 6px; border: 1px solid #fca5a5; margin-top: 8px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

st.title("⚙️ AISC-Thai Senior Engineer Connection Platform")
st.caption("ระบบวิเคราะห์แผ่นฐานเสารายพิกัดโบลต์อิสระ และแยกสถานะความเค้นรอยเชื่อมขั้นสูงตามหลักกลศาสตร์สากล")

# ==========================================
# 2. SEEDING & CONTROL PANEL (LEFT SIDE)
# ==========================================
col_ctrl, col_view = st.columns([1.1, 0.9])

with col_ctrl:
    st.markdown("<div class='step-header'>1. เลือกหน้าตัดเหล็ก มอก. และระบุแรงประลัย (LRFD)</div>", unsafe_allow_html=True)
    
    # 🌟 [PRESET BACK] ระบบเลือกหน้าตัดอัตโนมัติ
    selected_profile = st.selectbox("เลือกหน้าตัดเสาเหล็กคู่ต่อ (H-Beam มอก.):", list(THAI_H_BEAM_PROFILES.keys()), index=2)
    prof = THAI_H_BEAM_PROFILES[selected_profile]
    
    c1, c2, c3, c4 = st.columns(4)
    d = c1.number_input("ความลึก d (mm)", value=prof["d"])
    bf = c2.number_input("กว้างปีก bf (mm)", value=prof["bf"])
    tw = c3.number_input("หนาเอว tw (mm)", value=prof["tw"])
    tf = c4.number_input("หนาปีก tf (mm)", value=prof["tf"])

    cx1, cx2, cx3, cx4 = st.columns(4)
    p_u_kn = cx1.number_input("แรงกด Pu (kN)", value=450.0)
    v_u_kn = cx2.number_input("แรงเฉือน Vu (kN)", value=120.0)
    m_u_knm = cx3.number_input("โมเมนต์ Mu (kN-m)", value=135.0)
    fc_mpa = cx4.number_input("คอนกรีต fc' (MPa)", value=28.0)

    st.markdown("<div class='step-header'>2. แนะนำมิติแผ่นเหล็กฐานเพลต (Base Plate Dimension)</div>", unsafe_allow_html=True)
    
    # 🌟 [RECOMMENDATION SYSTEM BACK] แนะนำขนาดเพลตขั้นต่ำที่เหมาะสมโดยไม่ชนแนวขันประเจ
    rec_B = math.ceil((bf + 140) / 10) * 10
    rec_N = math.ceil((d + 160) / 10) * 10
    st.markdown(f"<div class='rec-box'>💡 ขนาดแนะนำสำหรับแผ่นฐาน: กว้าง B ≥ {rec_B} mm | ยาว N ≥ {rec_N} mm (เพื่อให้พ้นระยะขันโบลต์)</div>", unsafe_allow_html=True)
    
    cp1, cp2, cp3, cp4 = st.columns(4)
    B = cp1.number_input("ความกว้างใช้งาน B (mm)", value=float(rec_B))
    N = cp2.number_input("ความยาวใช้งาน N (mm)", value=float(rec_N))
    tp = cp3.selectbox("ความหนาเพลตใช้งาน tp (mm)", THAI_PLATE_THICKNESSES, index=2)
    bolt_name = cp4.selectbox("ขนาดสลักเกลียว", list(THAI_ANCHOR_BOLTS.keys()), index=2)
    bolt_profile = THAI_ANCHOR_BOLTS[bolt_name]

    st.markdown("<div class='step-header'>3. ตารางพิกัดโบลต์รายตัวแบบอิสระ (Dynamic Matrix Editor)</div>", unsafe_allow_html=True)
    st.caption("พิมพ์แก้ไขพิกัด X, Y บนแผ่นเพลตได้อิสระ โดยจุด (0,0) อยู่ที่จุดศูนย์กลางของเสาเหล็กพอดี")
    
    # 🌟 [SMART BOLT POSITION RECOMMENDATION] คำนวณพิกัดแนะนำเริ่มต้นหลบเหล็กเสาให้เลย
    safe_bolt_x = (bf / 2.0) + 45.0
    safe_bolt_y = (d / 2.0) + 50.0
    
    # หากกดเปลี่ยนหน้าตัดเสา ข้อมูลพิกัดแนะนำเริ่มต้นจะสไลด์หลบเสาอัตโนมัติ ไม่ตัดเข้าเนื้อเหล็กชัวร์!
    if "current_profile" not in st.session_state or st.session_state["current_profile"] != selected_profile:
        st.session_state["current_profile"] = selected_profile
        st.session_state["bolt_data"] = pd.DataFrame({
            "Bolt ID": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "X (mm)": [-safe_bolt_x, safe_bolt_x, -safe_bolt_x, safe_bolt_x, -safe_bolt_x, safe_bolt_x],
            "Y (mm)": [safe_bolt_y, safe_bolt_y, 0.0, 0.0, -safe_bolt_y, -safe_bolt_y]
        })

    edited_df = st.data_editor(st.session_state["bolt_data"], num_rows="dynamic", use_container_width=True)
    num_bolts = len(edited_df)

    # ตรวจสอบการชนเหล็กรายตัว (Geometrical Guardrail)
    interference_alerts = []
    for _, row in edited_df.iterrows():
        bx, by, bid = row["X (mm)"], row["Y (mm)"], row["Bolt ID"]
        if (abs(by) <= (d/2.0) + 35.0) and (abs(bx) <= (bf/2.0) + 35.0):
            # ตรวจสอบว่าโบลต์หลุดเข้าไปในพื้นที่เนื้อเหล็ก H-Beam หรือไม่
            if abs(by) > ((d/2.0) - tf) or abs(bx) < (tw/2.0) + 35.0:
                interference_alerts.append(f"❌ <b>{bid}</b> อยู่ที่พิกัด ({bx}, {by}) ชนแนวปีก/เอวเสาเหล็กหรือชิดเกินไปประแจขันไม่ได้!")
                
    if interference_alerts:
        st.markdown("<div class='danger-box'>" + "<br>".join(interference_alerts) + "</div>", unsafe_allow_html=True)

    st.markdown("<div class='step-header'>4. มิติรอยเชื่อม Fillet Weld รอยต่อหน้างาน</div>", unsafe_allow_html=True)
    weld_size_mm = st.slider("ระบุขนาดรอยเชื่อมขา Fillet (mm) ที่เลือกใช้จริง:", 3, 16, 8)

# ==========================================
# 3. ENGINEERING CORE MECHANICS (RIGHT SIDE)
# ==========================================
with col_view:
    P_u_n = p_u_kn * 1000.0
    V_u_n = v_u_kn * 1000.0
    M_u_nmm = m_u_knm * 1000000.0

    # 3.1 แรงดึงรายโบลต์ด้วยทฤษฎีกลุ่มตัวแปรร่วมเชิงพิกัด
    I_y_group = sum(edited_df["Y (mm)"]**2) if num_bolts > 0 else 1.0
    tensions = []
    for y in edited_df["Y (mm)"]:
        t_f = ((M_u_nmm * y) / I_y_group) + (-P_u_n / num_bolts) if num_bolts > 0 else 0
        tensions.append(max(0.0, t_f / 1000.0))
    edited_df["Tension (kN)"] = tensions

    # 3.2 การคำนวณแยกแยะความเค้นรอยเชื่อมอย่างละเอียด (Weld Partitioning Mechanics)
    l_flange = 4.0 * bf  # ความยาวรอยเชื่อมปีกรวม (นอกและในของปีกทั้งสองข้าง)
    l_web = 2.0 * (d - (2.0 * tf)) if (d - (2.0 * tf)) > 0 else 1.0  # ความยาวรอยเชื่อมเอวรวม (ซ้ายขวา)
    l_total = l_flange + l_web

    # แยกพฤติกรรมแรงกระทำต่อมิลลิเมตร (Weld Force Distribution Demand)
    weld_stress_axial = (P_u_n / l_total) / 1000.0 if l_total > 0 else 0  # kN/mm (กระจายลงทุกส่วน)
    weld_stress_moment = (M_u_nmm / (2.0 * bf * (d - tf))) / 1000.0 if bf > 0 else 0  # kN/mm (ลงปีกเท่านั้น)
    weld_stress_shear = (V_u_n / l_web) / 1000.0 if l_web > 0 else 0  # kN/mm (ลงเอวเท่านั้น)

    # รวมผลลัพธ์แยกตามชิ้นส่วน
    total_demand_flange = weld_stress_axial + weld_stress_moment  # รวมแนวแกนดิ่งที่ปีกเสา
    total_demand_web = math.sqrt(weld_stress_axial**2 + weld_stress_shear**2)  # รวมแรงเฉือนกับแรงกดที่เอวเสา
    
    max_weld_demand = max(total_demand_flange, total_demand_web)
    
    # กำลังวัสดุรอยเชื่อมตามมาตรฐาน AISC LRFD ($\phi R_n$)
    weld_cap_per_mm = 0.75 * 0.60 * 490.0 * 0.707 * weld_size_mm / 1000.0  # kN/mm
    
    # ขนาดรอยเชื่อมขั้นต่ำตามกฎ AISC Table J2.4 (พิจารณาจากความหนาแผ่นเพลตที่เชื่อมต่อ)
    if tp <= 6: min_weld_req = 3
    elif tp <= 13: min_weld_req = 5
    elif tp <= 19: min_weld_req = 6
    else: min_weld_req = 8
    
    # ขนาดรอยเชื่อมขั้นต่ำที่ต้องการในเชิงความแข็งแรง (Strength Required Weld Size)
    strength_weld_req = max_weld_demand / (0.75 * 0.60 * 490.0 * 0.707 / 1000.0)
    final_recommended_weld = max(min_weld_req, math.ceil(strength_weld_req))

    # 3.3 การเช็กหน่วยแรงกดคอนกรีตและการโก่งเพลต
    phi_c = 0.65
    f_p_max = phi_c * 0.85 * fc_mpa
    ecc = M_u_nmm / P_u_n if P_u_n > 0 else 0.0
    Y_length = N if ecc <= (N/6.0) else max(0.0, (N/2.0) - (P_u_n / (2.0 * B * f_p_max)))
    bearing_actual = P_u_n / (B*N) if ecc <= (N/6.0) else f_p_max
    
    m_arm = (N - 0.95 * d) / 2.0
    n_arm = (B - 0.80 * bf) / 2.0
    t_req = max(m_arm, n_arm) * math.sqrt((2.0 * bearing_actual) / (0.90 * 245.0))

    # ==========================================
    # 4. SENIOR ENGINEER EXECUTIVE SUMMARY REPORT
    # ==========================================
    st.markdown("<div class='report-title'>📊 รายงานการแจกแจงพฤติกรรมรอยเชื่อมและจุดต่อ</div>", unsafe_allow_html=True)
    
    # ตารางจำแนกแรงและส่วนรับแรงของรอยเชื่อมตามที่ขอ
    weld_breakdown_data = [
        {"ส่วนประกอบแนวเชื่อม": "รอยเชื่อมปีกเสา (Flange Weld)", "แรงดึง/กด จาก Moment": f"{weld_stress_moment:.3f} kN/mm", "แรงเฉือน จาก Shear Load": "0.000 kN/mm (ไม่คิด)", "แรงลัพธ์รวมชิ้นส่วน": f"{total_demand_flange:.3f} kN/mm"},
        {"ส่วนประกอบแนวเชื่อม": "รอยเชื่อมเอวเสา (Web Weld)", "แรงดึง/กด จาก Moment": "0.000 kN/mm (ไม่คิด)", "แรงเฉือน จาก Shear Load": f"{weld_stress_shear:.3f} kN/mm", "แรงลัพธ์รวมชิ้นส่วน": f"{total_demand_web:.3f} kN/mm"}
    ]
    st.table(pd.DataFrame(weld_breakdown_data))
    
    # 🌟 [DECISION BOX] ฟันธงขนาดรอยเชื่อมที่ควรใช้ให้ทันทีตามกฎวิศวกรรมควบคุม
    st.markdown(f"""
    <div class='rec-box'>
    <b>📋 สรุปผลการพิจารณาขนาดแนวเชื่อมที่ต้องใช้จริงหน้างาน:</b><br>
    - ขนาดขั้นต่ำตามมิติความหนาเพลต (AISC J2.4 Geometric Min): <b>{min_weld_req} mm</b><br>
    - ขนาดขั้นต่ำที่ต้องการเพื่อต้านทานแรงประลัย (Structural Strength Min): <b>{strength_weld_req:.1f} mm</b><br>
    🎯 <b>ข้อเสนอแนะสุดท้ายจากวิศวกรอาวุโส: ควรระบุขนาดรอยเชื่อมที่แบบขยายโครงสร้างเท่ากับ {final_recommended_weld} mm</b>
    </div>
    """, unsafe_allow_html=True)

    # ตารางสรุปภาพรวมความปลอดภัยของชิ้นส่วนอื่นๆ (Safety Matrix)
    st.markdown("<div class='report-title'>🛡️ ตารางประเมินระดับความปลอดภัยจุดต่อ (AISC Safety Check)</div>", unsafe_allow_html=True)
    max_t_actual = max(tensions) if tensions else 0
    bolt_t_cap = (0.75 * bolt_profile["F_nt"] * bolt_profile["area"]) / 1000.0
    
    summary_matrix = [
        {"รายการตรวจสอบ": "1. แรงกดปะทะผิวคอนกรีตฐานราก", "แรงที่เกิดขึ้นจริง": f"{bearing_actual:.1f} MPa", "ขีดกำลังที่รับได้สูงสุด": f"{f_p_max:.1f} MPa", "ผลลัพธ์ LRFD": "✅ PASS" if bearing_actual<=f_p_max else "❌ FAIL"},
        {"รายการตรวจสอบ": "2. ความหนาแผ่นเหล็กเพลตฐาน (tp)", "แรงที่เกิดขึ้นจริง": f"{t_req:.1f} mm", "ขีดกำลังที่รับได้สูงสุด": f"{tp:.1f} mm", "ผลลัพธ์ LRFD": "✅ PASS" if t_req<=tp else "❌ FAIL"},
        {"รายการตรวจสอบ": "3. กำลังรับแรงดึงสลักเกลียวตัววิกฤต", "แรงที่เกิดขึ้นจริง": f"{max_t_actual:.1f} kN", "ขีดกำลังที่รับได้สูงสุด": f"{bolt_t_cap:.1f} kN", "ผลลัพธ์ LRFD": "✅ PASS" if max_t_actual<=bolt_t_cap else "❌ FAIL"},
        {"รายการตรวจสอบ": "4. ขีดความสามารถแนวเชื่อมที่เลือกใช้งาน", "แรงที่เกิดขึ้นจริง": f"{max_weld_demand:.2f} kN/mm", "ขีดกำลังที่รับได้สูงสุด": f"{weld_cap_per_mm:.2f} kN/mm", "ผลลัพธ์ LRFD": "✅ PASS" if max_weld_demand<=weld_cap_per_mm else "❌ FAIL"}
    ]
    st.dataframe(pd.DataFrame(summary_matrix), use_container_width=True)

    # ==========================================
    # 5. BULLETPROOF GRAPHICS RESURRECTION
    # ==========================================
    st.markdown("<div class='report-title'>🧊 แบบจำลองแรงและแนวเชื่อม 3 มิติความละเอียดสูง</div>", unsafe_allow_html=True)
    
    # สร้างโมเดลจำลองด้วยระบบลากเส้นแบบถึก (Custom Drawn Lines + Heads) เพื่อให้ลูกศรขึ้นบนคลาวด์ชัวร์ 100%
    fig = go.Figure()
    
    # แผ่นเพลตและบล็อกเสา
    fig.add_trace(go.Mesh3d(x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2], y=[-N/2, -N/2, N/2, N/2, -N/2, -N/2, N/2, N/2], z=[0, 0, 0, 0, tp, tp, tp, tp], color='#64748b', opacity=0.85, name='Plate'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[-d/2, -d/2, -d/2+tf, -d/2+tf, -d/2, -d/2, -d/2+tf, -d/2+tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', name='Column'))
    fig.add_trace(go.Mesh3d(x=[-bf/2, bf/2, bf/2, -bf/2, -bf/2, bf/2, bf/2, -bf/2], y=[d/2-tf, d/2-tf, d/2, d/2, d/2-tf, d/2-tf, d/2, d/2], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#1e293b', showlegend=False))
    fig.add_trace(go.Mesh3d(x=[-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2], y=[-d/2+tf, -d/2+tf, d/2-tf, d/2-tf, -d/2+tf, -d/2+tf, d/2-tf, d/2-tf], z=[tp, tp, tp, tp, tp+400, tp+400, tp+400, tp+400], color='#334155', showlegend=False))

    # ไฮไลต์เส้นแนวรอยเชื่อม (Weld Lines Highlight)
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[-d/2, -d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), name='Flange Weld (Resist M+P)'))
    fig.add_trace(go.Scatter3d(x=[-bf/2, bf/2], y=[d/2, d/2], z=[tp+2, tp+2], mode='lines', line=dict(color='#06b6d4', width=8), showlegend=False))
    fig.add_trace(go.Scatter3d(x=[tw/2, tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), name='Web Weld (Resist V+P)'))
    fig.add_trace(go.Scatter3d(x=[-tw/2, -tw/2], y=[-d/2+tf, d/2-tf], z=[tp+2, tp+2], mode='lines', line=dict(color='#a855f7', width=6), showlegend=False))

    # พลอตสลักเกลียวรายพิกัด
    for _, row in edited_df.iterrows():
        bx, by, tf_bolt, b_id = row["X (mm)"], row["Y (mm)"], row["Tension (kN)"], row["Bolt ID"]
        bolt_col = '#ef4444' if tf_bolt > 0 else '#22c55e'
        fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[-200, tp+30], mode='lines+markers', marker=dict(size=6, color=bolt_col), line=dict(color=bolt_col, width=6), showlegend=False))
        
        # วาดเวกเตอร์แรงดึงถอนของโบลต์รายตัวด้วยระบบถึก (Line + Cone Target)
        if tf_bolt > 0:
            z_top = tp + 30 + 50 + (tf_bolt * 1.2)
            fig.add_trace(go.Scatter3d(x=[bx, bx], y=[by, by], z=[tp+30, z_top], mode='lines', line=dict(color='#b91c1c', width=10), showlegend=False))
            fig.add_trace(go.Cone(x=[bx], y=[by], z=[z_top], u=[0], v=[0], w=[40], sizemode="absolute", sizeref=25, showscale=False, colorscale=[[0,'#b91c1c'],[1,'#b91c1c']], showlegend=False))

    # 🌟 [CURE FOR MISSING ARROWS] วาดลูกศรแรงโหลดหลักระบบประลัยแบบคัสตอมเส้นหนาสุดๆ ไม่หายแน่นอน
    # 1. แรงกด Pu (แกนดิ่ง พุ่งลงสีดำ)
    fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[tp+550, tp+400], mode='lines', line=dict(color='black', width=12), name='Pu Force Vector'))
    fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+400], u=[0], v=[0], w=[-50], sizemode="absolute", sizeref=35, showscale=False, colorscale=[[0,'black'],[1,'black']], showlegend=False))

    # 2. แรงเฉือน Vu (แกนนอน พุ่งเข้าสีม่วง)
    if v_u_kn > 0:
        fig.add_trace(go.Scatter3d(x=[0,0], y=[-150,0], z=[tp+400, tp+400], mode='lines', line=dict(color='#9333ea', width=12), name='Vu Force Vector'))
        fig.add_trace(go.Cone(x=[0], y=[0], z=[tp+400], u=[0], v=[50], w=[0], sizemode="absolute", sizeref=35, showscale=False, colorscale=[[0,'#9333ea'],[1,'#9333ea']], showlegend=False))

    fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.3, y=-1.3, z=1.1))), margin=dict(l=0, r=0, b=0, t=0), height=600)
    st.plotly_chart(fig, use_container_width=True)
