# engine.py
import math

class AISC_LRFD_Engine:
    def __init__(self):
        # ค่า Factor ความปลอดภัย (Phi) ตามมาตรฐาน AISC 360
        self.phi_bolt_shear = 0.75
        self.phi_bolt_tension = 0.75
        self.phi_weld = 0.75

    def calculate_bolt_shear_capacity(self, bolt_diameter, bolt_grade, threads_excluded=True, planes=1):
        """
        คำนวณกำลังรับแรงเฉือนของนอต 1 ตัว ตาม AISC 360 Chapter J3
        bolt_diameter: ขนาดเส้นผ่านศูนย์กลาง (นิ้ว) เช่น 0.75, 0.875
        bolt_grade: 'A325' หรือ 'A490'
        threads_excluded: True ถ้าเกลียวอยู่นอกระนาบเฉือน (Group A-X), False ถ้าเกลียวอยู่ในระนาบเฉือน (Group A-N)
        planes: จำนวนระนาบรับแรงเฉือน (1 = Single Shear, 2 = Double Shear)
        """
        # 1. หาพื้นที่หน้าตัดของนอต (Nominal Bolt Area, Ab)
        A_b = (math.pi * (bolt_diameter ** 2)) / 4
        
        # 2. กำหนดค่า Nominal Shear Stress (Fnv) ตามตาราง Table J3.2
        if bolt_grade == 'A325':
            F_nv = 68.0 if threads_excluded else 54.0  # หน่วย ksi
        elif bolt_grade == 'A490':
            F_nv = 84.0 if threads_excluded else 68.0  # หน่วย ksi
        else:
            raise ValueError("รองรับเฉพาะเกลียวเกรด A325 และ A490")
            
        # 3. คำนวณกำลังรับแรงเฉือนปรับด้วยค่า Phi (Rn = phi * Fnv * Ab * จำนวนระนาบ)
        nominal_capacity = F_nv * A_b * planes
        design_capacity = self.phi_bolt_shear * nominal_capacity
        
        return {
            "A_b": round(A_b, 4),
            "F_nv": F_nv,
            "nominal_capacity_kips": round(nominal_capacity, 2),
            "design_capacity_kips": round(design_capacity, 2)
        }

    def calculate_weld_capacity(self, weld_size_sixteenths, weld_length, electrode_grade='E70'):
        """
        คำนวณกำลังรับแรงของรอยเชื่อมฟิลเลท (Fillet Weld) ตาม AISC 360 Chapter J2
        weld_size_sixteenths: ขนาดขาของรอยเชื่อม หน่วยเป็นเศษ 1 ส่วน 16 นิ้ว (เช่น ขนาด 1/4 นิ้ว คือ เลข 4)
        weld_length: ความยาวรอยเชื่อม (นิ้ว)
        electrode_grade: เกรดลวดเชื่อม เช่น 'E70' (Fu = 70 ksi)
        """
        if electrode_grade != 'E70':
            raise ValueError("เวอร์ชันนี้รองรับเฉพาะลวดเชื่อม E70")
            
        F_exx = 70.0  # ksi
        
        # 1. หาขนาดขาเชื่อมจริง (นิ้ว)
        weld_size_inch = weld_size_sixteenths / 16.0
        
        # 2. หาความหนาประสิทธิผลของรอยเชื่อม (Effective Throat, t) = ขาเชื่อม * sin(45องศา)
        effective_throat = weld_size_inch * 0.707
        
        # 3. หาหน่วยแรงเฉือนที่ยอมให้ของรอยเชื่อม (F_nw) = 0.60 * F_exx
        F_nw = 0.60 * F_exx
        
        # 4. คำนวณกำลังรับแรงรวมปรับด้วยค่า Phi (Rn = phi * F_nw * effective_throat * ความยาว)
        nominal_capacity = F_nw * effective_throat * weld_length
        design_capacity = self.phi_weld * nominal_capacity
        
        return {
            "weld_size_inch": round(weld_size_inch, 3),
            "effective_throat": round(effective_throat, 3),
            "nominal_capacity_kips": round(nominal_capacity, 2),
            "design_capacity_kips": round(design_capacity, 2)
        }
        
    def calculate_base_plate_bearing(self, B, N, fc_prime):
        """
        คำนวณกำลังรับแรงแบกทานของคอนกรีตใต้ Base Plate ตาม AISC LRFD J8
        B: ความกว้างแผ่นฐาน (นิ้ว)
        N: ความยาวแผ่นฐาน (นิ้ว)
        fc_prime: กำลังอัดของคอนกรีต (ksi) เช่น 240 ksc -> ประมาณ 3.5 ksi
        """
        phi_c = 0.65  # Factor สำหรับ Bearing บนคอนกรีต (LRFD)
        
        # พื้นที่แผ่นฐาน (A1)
        A1 = B * N
        
        # สมมติฐานแบบอนุรักษ์นิยม (Conservative): พื้นที่ฐานราก (A2) = พื้นที่แผ่นฐาน (A1)
        # สมการ: Pp = 0.85 * fc' * A1
        nominal_capacity = 0.85 * fc_prime * A1
        design_capacity = phi_c * nominal_capacity
        
        return {
            "A1": round(A1, 2),
            "nominal_capacity_kips": round(nominal_capacity, 2),
            "design_capacity_kips": round(design_capacity, 2)
        }
    def calculate_base_weld(self, d, bf, tf, tw, weld_size, p_u, v_u, m_u):
        """
        ประเมินกำลังรอยเชื่อมรอบโคนเสาแบบง่าย (Simplified Perimeter Weld)
        สมมติว่าเชื่อมรอบรูป (All-around fillet weld)
        """
        # คำนวณความยาวรอยเชื่อมรวมโดยประมาณ (หักมุมตััดต่างๆ ออกเล็กน้อย)
        L_w = (4 * bf) + (2 * d) - (2 * tw) 
        
        # ใช้สมการรอยเชื่อมเดิมที่มีอยู่แล้ว
        res_weld = self.calculate_weld_capacity(weld_size, L_w, 'E70')
        capacity = res_weld["design_capacity_kips"]
        
        # สมมติฐานรับแรงเฉือนรวมเป็นหลัก (ในเวอร์ชัน MVP)
        # หากจะคิดเรื่องโมเมนต์ ต้องหา Section Modulus ของกลุ่มรอยเชื่อม (Sw) ซึ่งจะซับซ้อนขึ้น
        return capacity, L_w

    def calculate_anchor_bolt_tension(self, B, N, m_u, p_u, num_bolts):
        """
        คำนวณแรงดึงสูงสุดในนอตฝังเมื่อเกิดโมเมนต์ (Simplified Lever Arm Method)
        """
        # สมมติระยะคานงัด (Lever Arm, y) ห่างจากขอบประมาณ 2 นิ้ว
        lever_arm = N - 4.0 
        
        # แรงดึงจากโมเมนต์ หักล้างด้วยแรงกด P_u (กระจายลงนอตครึ่งหนึ่ง)
        T_u_total = (m_u / lever_arm) - (p_u / 2)
        
        if T_u_total <= 0:
            return 0.0 # ไม่มีแรงดึง นอตรับแค่ Shear
            
        # สมมติว่านอตฝั่งที่รับแรงดึงมีจำนวนครึ่งหนึ่งของทั้งหมด
        T_u_per_bolt = T_u_total / (num_bolts / 2)
        return round(T_u_per_bolt, 2)
