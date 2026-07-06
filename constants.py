# constants.py
"""
Reference data / lookup tables for the AISC steel-connection engine.

Keeping all "database" style constants in one module makes it easy to
add a new bolt, plate, or steel grade without touching any calculation
or UI code.
"""

THAI_H_BEAM_PROFILES = {
    "H 200x200x8x12": {"d": 200.0, "bf": 200.0, "tw": 8.0, "tf": 12.0},
    "H 250x250x9x14": {"d": 250.0, "bf": 250.0, "tw": 9.0, "tf": 14.0},
    "H 300x300x10x15": {"d": 300.0, "bf": 300.0, "tw": 10.0, "tf": 15.0},
    "H 350x350x12x19": {"d": 350.0, "bf": 350.0, "tw": 12.0, "tf": 19.0},
    "H 400x400x13x21": {"d": 400.0, "bf": 400.0, "tw": 13.0, "tf": 21.0},
}

# F_nt / F_nv are nominal stresses (MPa), area is nominal bolt area (mm^2)
THAI_ANCHOR_BOLTS = {
    "M16 (Grade 4.6)": {"dia": 16.0, "area": 157.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 22.0},
    "M20 (Grade 4.6)": {"dia": 20.0, "area": 245.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 26.0},
    "M24 (Grade 4.6)": {"dia": 24.0, "area": 353.0, "F_nt": 300.0, "F_nv": 180.0, "min_edge": 32.0},
    "M30 (Grade 8.8)": {"dia": 30.0, "area": 561.0, "F_nt": 600.0, "F_nv": 360.0, "min_edge": 38.0},
    "M36 (Grade 8.8)": {"dia": 36.0, "area": 817.0, "F_nt": 600.0, "F_nv": 360.0, "min_edge": 46.0},
}

THAI_PLATE_THICKNESSES = [12, 16, 19, 22, 25, 28, 32, 38, 50]

STEEL_PLATE_GRADES = {
    "SS400 (Fy = 245 MPa)": {"Fy": 245.0, "Fu": 400.0},
    "SM490 (Fy = 325 MPa)": {"Fy": 325.0, "Fu": 490.0},
    "SM520 (Fy = 365 MPa)": {"Fy": 365.0, "Fu": 520.0},
}

WELD_ELECTRODE_GRADES = {
    "E70XX (F_exx = 490 MPa)": {"F_exx": 490.0},
    "E60XX (F_exx = 415 MPa)": {"F_exx": 415.0},
    "E80XX (F_exx = 550 MPa)": {"F_exx": 550.0},
}

# ---- Shared design factors (kept here so a single source of truth exists) ----
PHI_BOLT = 0.75          # AISC J3 resistance factor for bolt tension/shear
PHI_CONCRETE_BEARING = 0.65   # AISC J8 concrete bearing
PHI_WELD = 0.75          # AISC J2 weld resistance factor
PHI_ANCHOR_PULLOUT = 0.70     # ACI 318 Chapter 17, pullout
PHI_ANCHOR_BREAKOUT = 0.70    # ACI 318 Chapter 17, concrete breakout
