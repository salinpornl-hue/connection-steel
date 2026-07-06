# tests/test_calculations.py
"""
Basic correctness/regression tests for calculations.py.

Run with:  pytest -q
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from calculations import (
    bolt_steel_capacities,
    check_bolt_geometry,
    check_concrete_capacities,
    compute_bearing_regime,
    default_bolt_layout,
    default_plate_size,
    design_perimeter_weld,
    plate_thickness_compression_side,
    plate_thickness_tension_side,
    solve_bearing_block_bolts,
)


# ---------------- bearing regime ----------------

def test_bearing_no_compression_when_no_axial_load():
    r = compute_bearing_regime(P_u_n=0, M_u_nmm=1e6, B=500, N=600, fc_mpa=28)
    assert r.case == "no-compression"
    assert not r.ok


def test_bearing_full_contact_small_eccentricity():
    # e = 0 -> pure axial, well inside kern -> full contact
    r = compute_bearing_regime(P_u_n=500_000, M_u_nmm=0, B=500, N=600, fc_mpa=28)
    assert r.case == "full"
    assert r.f_p_peak > 0


def test_bearing_uplift_when_eccentricity_exceeds_half_N():
    r = compute_bearing_regime(P_u_n=1000, M_u_nmm=1e9, B=500, N=600, fc_mpa=28)
    assert r.case == "uplift"
    assert not r.ok


# ---------------- bolt bearing-block solver ----------------

def test_solver_bearing_only_when_small_moment():
    coords = [(-100, 100), (100, 100), (-100, -100), (100, -100)]
    res = solve_bearing_block_bolts(P_u=500_000, M_u=1e6, B=500, N=600, bolt_coords=coords, q_max=15.0)
    assert res.ok
    assert res.case == "bearing-only"
    assert all(t == 0.0 for t in res.tensions)


def test_solver_uplift_solution_satisfies_equilibrium():
    coords = [(-150, 200), (150, 200), (-150, -200), (150, -200)]
    P_u = 200_000.0
    M_u = 150_000_000.0
    res = solve_bearing_block_bolts(P_u=P_u, M_u=M_u, B=500, N=600, bolt_coords=coords, q_max=15.0)
    assert res.ok
    assert res.case == "uplift"
    # equilibrium residuals should be near zero
    assert abs(res.resid_F) < 1.0  # within 1 N
    assert abs(res.resid_M) < 1000.0  # within 1000 N*mm out of ~1e8 N*mm demand


def test_solver_handles_zero_bolts():
    res = solve_bearing_block_bolts(P_u=1000, M_u=1000, B=500, N=600, bolt_coords=[], q_max=15.0)
    assert not res.ok
    assert res.case == "no-bolts"


def test_solver_never_raises_zero_division_for_degenerate_layout():
    # All bolts on the neutral axis edge case shouldn't crash
    coords = [(0, 0), (0, 0)]
    res = solve_bearing_block_bolts(P_u=10, M_u=1e7, B=500, N=600, bolt_coords=coords, q_max=15.0)
    assert isinstance(res.tensions, list)


# ---------------- weld design ----------------

def test_weld_pass_with_generous_size():
    res = design_perimeter_weld(
        P_u_n=500_000, V_u_n=100_000, M_u_nmm=140_000_000,
        d=300, bf=300, tf=15, weld_size_mm=16, F_exx=490, tp=22,
    )
    assert res.passes
    assert res.recommended_size >= res.min_size_constructability


def test_weld_fail_with_tiny_size():
    res = design_perimeter_weld(
        P_u_n=500_000, V_u_n=100_000, M_u_nmm=140_000_000,
        d=300, bf=300, tf=15, weld_size_mm=3, F_exx=415, tp=22,
    )
    assert not res.passes


# ---------------- plate thickness ----------------

def test_plate_thickness_compression_scales_with_bearing_pressure():
    _, _, t_low = plate_thickness_compression_side(N=600, d=300, B=500, bf=300, f_p_peak=5, Fy_plate=245)
    _, _, t_high = plate_thickness_compression_side(N=600, d=300, B=500, bf=300, f_p_peak=15, Fy_plate=245)
    assert t_high > t_low


def test_plate_thickness_tension_zero_when_no_tension():
    max_t, f_arm, b_eff, t_req = plate_thickness_tension_side(
        bolt_tensions_and_y=[(0.0, 250), (0.0, -250)], d=300, B=500, Fy_plate=245,
    )
    assert max_t == 0.0
    assert t_req == 0.0


# ---------------- bolt steel capacities ----------------

def test_bolt_capacity_reduced_by_shear_interaction():
    res_no_shear = bolt_steel_capacities(F_nt=600, F_nv=360, A_b=353, V_u_kn=0.0, num_bolts=4)
    res_with_shear = bolt_steel_capacities(F_nt=600, F_nv=360, A_b=353, V_u_kn=200.0, num_bolts=4)
    assert res_with_shear.tension_capacity_with_shear_kN < res_no_shear.tension_capacity_with_shear_kN


# ---------------- concrete anchorage ----------------

def test_concrete_capacities_positive_for_valid_inputs():
    res = check_concrete_capacities(f_c_prime=28, h_ef=250, c_edge=200, d_b=24)
    assert res.phi_N_cb > 0
    assert res.phi_N_pn > 0


def test_concrete_capacities_rejects_nonpositive_strength():
    with pytest.raises(ValueError):
        check_concrete_capacities(f_c_prime=0, h_ef=250, c_edge=200, d_b=24)


def test_concrete_capacities_rejects_nonpositive_embedment():
    with pytest.raises(ValueError):
        check_concrete_capacities(f_c_prime=28, h_ef=0, c_edge=200, d_b=24)


# ---------------- geometry ----------------

def test_geometry_flags_short_edge_distance():
    # 10 mm from the +X plate edge, but clear of the column conflict zone
    bolts = [("B1", 240, 0)]
    errors = check_bolt_geometry(bolts, B=500, N=600, bf=300, d=300, min_edge_req=32, min_spacing_req=64)
    assert any("edge distance" in e for e in errors)


def test_geometry_flags_close_spacing():
    bolts = [("B1", 200, 200), ("B2", 201, 200)]
    errors = check_bolt_geometry(bolts, B=500, N=600, bf=100, d=100, min_edge_req=10, min_spacing_req=64)
    assert any("Spacing too close" in e for e in errors)


def test_geometry_passes_clean_layout():
    layout = default_bolt_layout(bf=300, d=300)
    bolts = [(row["Bolt ID"], row["X (mm)"], row["Y (mm)"]) for row in layout]
    B, N = default_plate_size(bf=300, d=300)
    errors = check_bolt_geometry(bolts, B=B, N=N, bf=300, d=300, min_edge_req=32, min_spacing_req=64)
    assert errors == []
