# calculations.py
"""
Pure engineering calculations for the AISC steel base-plate / anchor-bolt
connection design engine.

Every function here is a plain function of its inputs (no Streamlit, no
global state) so it can be unit tested and reused outside the web app.
All units are metric: force in N unless a "_kn"/"_knm" suffix says
otherwise, length in mm, stress in MPa (N/mm^2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from constants import (
    PHI_ANCHOR_BREAKOUT,
    PHI_ANCHOR_PULLOUT,
    PHI_BOLT,
    PHI_CONCRETE_BEARING,
    PHI_WELD,
)


# ============================================================
# Geometry / layout helpers
# ============================================================

def default_plate_size(bf: float, d: float) -> tuple[float, float]:
    """Suggest a starting plate width B and length N from column dimensions."""
    B = math.ceil((bf + 150.0) / 10.0) * 10.0
    N = math.ceil((d + 160.0) / 10.0) * 10.0
    return float(B), float(N)


def default_bolt_layout(bf: float, d: float) -> list[dict]:
    """
    Suggest a symmetric 6-bolt starting layout around the column.

    NOTE: with the 150/160 mm plate-size margins in default_plate_size,
    the bolt offset here must leave at least the default bolt's catalogue
    min-edge-distance clear of the plate edge, or the geometry checker
    flags the app's own default layout as failing on first load (this was
    a bug in the original: 45/50 mm margins left only 30 mm clearance,
    less than the 32 mm required by the default M24 bolt).
    """
    x = (bf / 2.0) + 40.0
    y = (d / 2.0) + 45.0
    ids = ["B1", "B2", "B3", "B4", "B5", "B6"]
    xs = [-x, x, -x, x, -x, x]
    ys = [y, y, 0.0, 0.0, -y, -y]
    return [{"Bolt ID": i, "X (mm)": px, "Y (mm)": py} for i, px, py in zip(ids, xs, ys)]


def check_bolt_geometry(
    bolts: Sequence[tuple[str, float, float]],
    B: float,
    N: float,
    bf: float,
    d: float,
    min_edge_req: float,
    min_spacing_req: float,
) -> list[str]:
    """
    Check plate-edge distance, column conflict zone, and bolt-to-bolt
    spacing for a list of (bolt_id, x, y) tuples.

    Returns a list of human-readable HTML error strings (empty if OK).
    """
    errors: list[str] = []

    for bid, bx, by in bolts:
        actual_min_edge = min((B / 2.0) - bx, bx - (-B / 2.0), (N / 2.0) - by, by - (-N / 2.0))
        if actual_min_edge < min_edge_req:
            errors.append(
                f"❌ <b>{bid}:</b> Plate edge distance too short "
                f"({actual_min_edge:.1f} mm < {min_edge_req:.1f} mm)"
            )
        if abs(by) <= (d / 2.0) + 35.0 and abs(bx) <= (bf / 2.0) + 35.0:
            errors.append(f"❌ <b>{bid}:</b> Falls inside the conflict zone — hits the column or too tight for a wrench")

    n = len(bolts)
    for i in range(n):
        for j in range(i + 1, n):
            _, x1, y1 = bolts[i]
            _, x2, y2 = bolts[j]
            dist = math.hypot(x1 - x2, y1 - y2)
            if dist < min_spacing_req:
                errors.append(
                    f"⚠️ <b>{bolts[i][0]}-{bolts[j][0]}:</b> Spacing too close "
                    f"({dist:.1f} mm < {min_spacing_req:.1f} mm)"
                )
    return errors


# ============================================================
# Weld design (AISC J2, elastic method)
# ============================================================

@dataclass
class WeldResult:
    l_flange: float
    l_web: float
    stress_axial: float
    stress_moment: float
    stress_shear: float
    demand_flange: float
    demand_web: float
    max_demand: float
    capacity_per_mm: float
    min_size_constructability: int
    strength_required_size: float
    recommended_size: int
    passes: bool


def design_perimeter_weld(
    P_u_n: float, V_u_n: float, M_u_nmm: float,
    d: float, bf: float, tf: float,
    weld_size_mm: float, F_exx: float, tp: float,
) -> WeldResult:
    """Elastic-method check of the column-to-plate perimeter fillet weld."""
    l_flange = 4.0 * bf
    l_web = 2.0 * (d - 2.0 * tf) if (d - 2.0 * tf) > 0 else 1.0
    l_total = l_flange + l_web

    stress_axial = (P_u_n / l_total) / 1000.0 if l_total > 0 else 0.0
    stress_moment = (M_u_nmm / (2.0 * bf * (d - tf))) / 1000.0 if bf > 0 and (d - tf) > 0 else 0.0
    stress_shear = (V_u_n / l_web) / 1000.0 if l_web > 0 else 0.0

    demand_flange = stress_axial + stress_moment
    demand_web = math.hypot(stress_axial, stress_shear)
    max_demand = max(demand_flange, demand_web)

    capacity_per_mm = PHI_WELD * 0.60 * F_exx * 0.707 * weld_size_mm / 1000.0

    min_size = 5 if tp <= 13 else (6 if tp <= 19 else 8)
    unit_capacity = PHI_WELD * 0.60 * F_exx * 0.707 / 1000.0
    strength_required_size = max_demand / unit_capacity if unit_capacity > 0 else 0.0
    recommended_size = max(min_size, math.ceil(strength_required_size))

    return WeldResult(
        l_flange=l_flange, l_web=l_web,
        stress_axial=stress_axial, stress_moment=stress_moment, stress_shear=stress_shear,
        demand_flange=demand_flange, demand_web=demand_web, max_demand=max_demand,
        capacity_per_mm=capacity_per_mm,
        min_size_constructability=min_size,
        strength_required_size=strength_required_size,
        recommended_size=recommended_size,
        passes=max_demand <= capacity_per_mm,
    )


# ============================================================
# Base-plate bearing pressure (rigid plate on concrete)
# ============================================================

@dataclass
class BearingResult:
    case: str          # "no-compression" | "full" | "partial" | "uplift"
    eccentricity: float
    e_kern: float
    e_edge: float
    f_p_peak: float
    f_p_min: float
    f_p_max_capacity: float
    Y_bearing: float
    ok: bool


def compute_bearing_regime(P_u_n: float, M_u_nmm: float, B: float, N: float, fc_mpa: float) -> BearingResult:
    """
    Classify the base-plate bearing regime (full contact / partial contact /
    uplift) and compute the resulting peak bearing pressure, following the
    standard rigid base-plate-on-concrete assumption (AISC Design Guide 1).
    """
    f_p_max = PHI_CONCRETE_BEARING * 0.85 * fc_mpa
    e_kern = N / 6.0
    e_edge = N / 2.0
    ecc = (M_u_nmm / P_u_n) if P_u_n > 0 else 0.0

    if P_u_n <= 0:
        return BearingResult("no-compression", ecc, e_kern, e_edge, 0.0, 0.0, f_p_max, 0.0, False)

    if ecc <= e_kern:
        q_mean = P_u_n / (B * N)
        f_p_min = q_mean * (1.0 - 6.0 * ecc / N)
        f_p_peak = q_mean * (1.0 + 6.0 * ecc / N)
        return BearingResult("full", ecc, e_kern, e_edge, f_p_peak, f_p_min, f_p_max, float(N), f_p_peak <= f_p_max)

    if ecc < e_edge:
        Y = 1.5 * N - 3.0 * ecc
        f_p_peak = (2.0 * P_u_n) / (B * Y) if Y > 0 else f_p_max
        return BearingResult("partial", ecc, e_kern, e_edge, f_p_peak, 0.0, f_p_max, Y, f_p_peak <= f_p_max)

    return BearingResult("uplift", ecc, e_kern, e_edge, f_p_max, 0.0, f_p_max, 0.0, False)


# ============================================================
# Bearing-block + bolt-group equilibrium solver
# ============================================================

@dataclass
class BoltEquilibriumResult:
    ok: bool
    case: str
    tensions: list[float]         # kN, one per bolt, in input order
    Y: "float | None" = None
    C: "float | None" = None
    k: "float | None" = None
    y_NA: "float | None" = None
    total_T_kN: float = 0.0
    resid_F: float = 0.0
    resid_M: float = 0.0
    reason: str = ""


def solve_bearing_block_bolts(
    P_u: float, M_u: float, B: float, N: float,
    bolt_coords: Sequence[tuple[float, float]], q_max: float,
) -> BoltEquilibriumResult:
    """
    Solve for the neutral axis / compression bearing-block length Y that
    equilibrates axial load P_u and moment M_u, then back out the tension
    in every bolt above the neutral axis (linear-elastic, plane-sections
    assumption per AISC Design Guide 1).

    Force units: P_u in N, M_u in N*mm, coordinates/B/N in mm, q_max in MPa.
    Returned tensions are in kN.
    """
    bolts = list(bolt_coords)
    n = len(bolts)
    if n == 0:
        return BoltEquilibriumResult(ok=False, case="no-bolts", tensions=[])

    Y_min = P_u / (q_max * B) if (q_max * B) > 0 else 0.0
    e = M_u / P_u if P_u > 0 else float("inf")

    if P_u > 0 and e <= N / 2.0:
        return BoltEquilibriumResult(
            ok=True, case="bearing-only", tensions=[0.0] * n,
            Y=None, C=P_u, y_NA=None, total_T_kN=0.0, resid_F=0.0, resid_M=0.0,
        )

    if Y_min >= N - 1.0:
        return BoltEquilibriumResult(
            ok=False, case="pu-too-large", tensions=[0.0] * n,
            reason="P_u exceeds max bearing (q_max*B*N); enlarge plate.",
        )

    def state(Y: float):
        y_NA = -N / 2.0 + Y
        tension_bolts = [y for (_, y) in bolts if y > y_NA + 1e-6]
        if not tension_bolts:
            return None
        C = q_max * B * Y
        arms = [y - y_NA for y in tension_bolts]
        arm_sum = sum(arms)
        k = max(0.0, (C - P_u) / arm_sum) if arm_sum > 0 else 0.0
        Ts = [k * a for a in arms]
        M_resist = C * (N / 2.0 - Y / 2.0) + sum(T * y for T, y in zip(Ts, tension_bolts))
        return y_NA, tension_bolts, Ts, C, k, M_resist

    Y_lo, Y_hi = max(Y_min, 1.0), N - 1.0
    samples = 400
    grid = [Y_lo + (Y_hi - Y_lo) * i / samples for i in range(samples + 1)]
    grid_states = [state(Y) for Y in grid]
    residuals = [(s[5] - M_u) if s else None for s in grid_states]

    solution = None
    Y_sol = None
    for i in range(samples):
        r1, r2 = residuals[i], residuals[i + 1]
        if r1 is None or r2 is None:
            continue
        if (r1 >= 0) != (r2 >= 0):
            lo, hi = grid[i], grid[i + 1]
            state_lo = state(lo)
            r_lo = (state_lo[5] - M_u) if state_lo else r1
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                s_mid = state(mid)
                r_mid = (s_mid[5] - M_u) if s_mid else r1
                if (r_lo >= 0) != (r_mid >= 0):
                    hi = mid
                else:
                    lo, r_lo = mid, r_mid
            Y_sol = 0.5 * (lo + hi)
            solution = state(Y_sol)
            break

    if solution is None:
        return BoltEquilibriumResult(
            ok=False, case="insufficient-capacity", tensions=[0.0] * n,
            reason="Bearing + bolts cannot develop M_u; add bolts/plate/anchor capacity.",
        )

    y_NA, tension_bolts, Ts, C, k, _ = solution
    tensions: list[float] = []
    ti = 0
    for (_, y) in bolts:
        if y > y_NA + 1e-6:
            tensions.append(Ts[ti] / 1000.0)
            ti += 1
        else:
            tensions.append(0.0)

    total_T = sum(Ts)
    resid_F = C - P_u - total_T
    resid_M = C * (N / 2.0 - Y_sol / 2.0) + sum(T * y for T, y in zip(Ts, tension_bolts)) - M_u

    return BoltEquilibriumResult(
        ok=True, case="uplift", tensions=tensions,
        Y=Y_sol, C=C, k=k, y_NA=y_NA, total_T_kN=total_T / 1000.0,
        resid_F=resid_F, resid_M=resid_M,
    )


# ============================================================
# Base-plate required thickness (AISC Design Guide 1)
# ============================================================

def plate_thickness_compression_side(N: float, d: float, B: float, bf: float, f_p_peak: float, Fy_plate: float) -> tuple[float, float, float]:
    """Return (m_arm, n_arm, t_req) for the compression-side plate check."""
    m_arm = (N - 0.95 * d) / 2.0
    n_arm = (B - 0.80 * bf) / 2.0
    t_req = max(m_arm, n_arm) * math.sqrt((2.0 * f_p_peak) / (0.90 * Fy_plate)) if f_p_peak > 0 else 0.0
    return m_arm, n_arm, t_req


def plate_thickness_tension_side(
    bolt_tensions_and_y: Sequence[tuple[float, float]], d: float, B: float, Fy_plate: float,
) -> tuple[float, float, float, float]:
    """
    Return (max_t_actual_kN, f_arm, b_eff, t_req) for the tension-side
    (prying / cantilever) plate check, using the bolt with the largest
    lever arm beyond the column flange.
    """
    max_t_actual = max((t for t, _ in bolt_tensions_and_y), default=0.0)
    f_arm = 0.0
    b_eff = 1.0
    t_req = 0.0
    if max_t_actual > 0:
        f_arm = max((max(0.0, abs(y) - d / 2.0) for t, y in bolt_tensions_and_y if t > 0), default=0.0)
        if f_arm > 0:
            b_eff = min(float(B), 3.5 * f_arm)
            M_u_tension = max_t_actual * 1000.0 * f_arm
            t_req = math.sqrt((4.0 * M_u_tension) / (0.90 * Fy_plate * b_eff))
    return max_t_actual, f_arm, b_eff, t_req


# ============================================================
# Anchor bolt steel capacities (AISC J3)
# ============================================================

@dataclass
class BoltCapacityResult:
    tension_capacity_kN: float
    shear_capacity_kN: float
    shear_per_bolt_kN: float
    f_rv: float
    F_nt_prime: float
    tension_capacity_with_shear_kN: float


def bolt_steel_capacities(F_nt: float, F_nv: float, A_b: float, V_u_kn: float, num_bolts: int) -> BoltCapacityResult:
    """
    Bolt tension/shear capacity, including the AISC J3.7 combined
    tension-and-shear interaction reduction.
    """
    tension_capacity = (PHI_BOLT * F_nt * A_b) / 1000.0
    shear_capacity = (PHI_BOLT * F_nv * A_b) / 1000.0
    shear_per_bolt = V_u_kn / num_bolts if num_bolts > 0 else 0.0

    f_rv = (shear_per_bolt * 1000.0) / A_b if A_b > 0 else 0.0
    F_nt_prime = 1.3 * F_nt - (F_nt / (PHI_BOLT * F_nv)) * f_rv if F_nv > 0 else F_nt
    F_nt_prime = min(F_nt, max(0.0, F_nt_prime))
    tension_capacity_with_shear = (PHI_BOLT * F_nt_prime * A_b) / 1000.0

    return BoltCapacityResult(
        tension_capacity_kN=tension_capacity,
        shear_capacity_kN=shear_capacity,
        shear_per_bolt_kN=shear_per_bolt,
        f_rv=f_rv,
        F_nt_prime=F_nt_prime,
        tension_capacity_with_shear_kN=tension_capacity_with_shear,
    )


# ============================================================
# Concrete anchorage capacities (ACI 318, simplified single-anchor)
# ============================================================

@dataclass
class ConcreteAnchorResult:
    phi_N_cb: float   # concrete breakout, kN
    phi_N_pn: float   # concrete pullout, kN


def check_concrete_capacities(f_c_prime: float, h_ef: float, c_edge: float, d_b: float) -> ConcreteAnchorResult:
    """
    Simplified single-anchor concrete breakout (ACI 318-19 Ch.17.6.2) and
    pullout (17.6.3) capacities for one anchor in tension.

    f_c_prime: concrete compressive strength, MPa (must be > 0)
    h_ef: embedment depth, mm
    c_edge: distance to the nearest free edge, mm
    d_b: anchor bolt diameter, mm
    """
    if f_c_prime <= 0:
        raise ValueError("f_c_prime (concrete strength) must be greater than zero.")
    if h_ef <= 0:
        raise ValueError("h_ef (embedment depth) must be greater than zero.")

    A_brg = 1.5 * (math.pi * (d_b ** 2) / 4.0)
    N_p = 8.0 * A_brg * f_c_prime
    phi_N_pn = (PHI_ANCHOR_PULLOUT * N_p) / 1000.0

    A_N0 = 9.0 * (h_ef ** 2)
    A_N = A_N0
    if c_edge < 1.5 * h_ef:
        A_N = (c_edge + 1.5 * h_ef) * (3.0 * h_ef)

    N_b = 10.0 * math.sqrt(f_c_prime) * (h_ef ** 1.5)

    psi_ed = 1.0
    if c_edge < 1.5 * h_ef:
        psi_ed = 0.7 + 0.3 * (c_edge / (1.5 * h_ef))

    N_cb = (A_N / A_N0) * psi_ed * N_b
    phi_N_cb = (PHI_ANCHOR_BREAKOUT * N_cb) / 1000.0

    return ConcreteAnchorResult(phi_N_cb=phi_N_cb, phi_N_pn=phi_N_pn)
