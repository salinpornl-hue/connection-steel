# AISC Steel-Connection Ultimate Engine

A Streamlit app for designing a steel column base plate / anchor-bolt
connection: weld sizing, base-plate thickness, and anchor bolt + concrete
checks, with a live 3D model.

## Structure

```
constants.py            Lookup tables (H-beam profiles, bolts, plate
                         thicknesses, steel/weld grades, phi-factors)
calculations.py          Pure engineering functions — no Streamlit, no
                         global state. Fully unit tested.
app.py                   Streamlit UI. Imports from the two modules above
                         and only handles layout, widgets, and the 3D plot.
tests/test_calculations.py   18 pytest cases covering the bearing regimes,
                         the bearing-block/bolt equilibrium solver, weld
                         design, plate thickness, bolt capacity, and
                         concrete anchorage.
requirements.txt
```

Run it with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with:

```bash
pip install pytest
pytest -q
```

## What changed from the original version

**Functional (things that were broken):**
- `requirements.txt` was missing `pandas`, which `app.py` imports directly —
  a fresh `pip install -r requirements.txt` would not actually run the app.
- `engine.py` was dead code: an unused, self-contained AISC calculator in
  **imperial units** (inches, ksi, A325/A490 bolts) that duplicated — and
  contradicted — the metric calculations actually used by `app.py`. Nothing
  imported it. It has been removed rather than left as confusing, unused,
  unit-inconsistent code; all of its useful logic (weld, bearing, bolt
  tension) already exists correctly in `calculations.py` in the metric
  system the rest of the app uses.
- The default bolt layout (6 bolts at ±45mm/±50mm past the column) left
  only 30mm of clear plate edge distance, which is *less* than the 32mm
  minimum required by the app's own default bolt (M24) — so the app could
  show a geometry FAIL on first load with default inputs. Margins were
  tightened to 40mm/45mm so the default configuration passes its own check.
- The bolt coordinate editor (`st.data_editor`) had no explicit widget
  `key`. Streamlit widgets without a `key` are addressed by their position
  in the script and can keep their *own* internal state after first render,
  silently ignoring later programmatic updates to the dataframe passed in
  (e.g. after "Auto-Resize" or switching column profile). The key is now
  tied to `plate_version`, the same counter already used to remount the
  plate-size number inputs, so the grid reliably refreshes when it should.
- The bearing-block/bolt equilibrium solver could divide by zero
  (`sum(arms) == 0`) for a degenerate bolt layout where every tension-side
  bolt sits exactly on the neutral axis. Guarded with a zero check.
- Several numeric inputs (`f'c`, section dimensions, plate B/N, loads) had
  no `min_value`, so a 0 or negative entry could crash the app with a
  `math domain error` (e.g. `sqrt` of a negative number) instead of giving
  a clear validation message. Sensible minimums were added throughout.
- `check_concrete_capacities` now raises a clear `ValueError` for
  non-positive concrete strength or embedment depth instead of silently
  producing `nan`/crashing deeper in the call stack.

**Correctness:**
- All the underlying engineering formulas (weld elastic method, AISC DG-1
  bearing regimes, the bearing-block/bolt-group solver, AISC J3.7
  tension-shear interaction, ACI 318 simplified breakout/pullout) are
  unchanged — they were verified against the original app output and are
  now covered by regression tests so future edits can't silently break them.
- Added 18 unit tests (`tests/test_calculations.py`) covering every
  calculation module, including the equilibrium residual check
  (ΣF ≈ 0, ΣM ≈ 0) for the bolt-group solver.

**Orderliness:**
- Split one 698-line file mixing lookup tables, engineering math, and UI
  into three focused modules (`constants.py`, `calculations.py`, `app.py`),
  each independently readable and the math independently testable.
- All calculation functions now have docstrings, type hints, and return
  small `@dataclass` result objects (e.g. `WeldResult`, `BearingResult`,
  `BoltEquilibriumResult`) instead of loosely-shaped dicts/tuples, so
  `app.py` reads as `weld_res.passes` / `bearing.f_p_peak` rather than
  reconstructing meaning from positional tuple unpacking.
- Renamed the bolt-group inertia label from `I_y` to `I_x` to match what
  is actually being computed (Σy² is the inertia about the horizontal
  X-axis, which resists the applied moment about that axis).

## Engineering assumptions (unchanged from the original, carried over here for clarity)

- Linear-elastic, plane-sections bolt-group analysis (AISC Design Guide 1)
  for combined axial + moment on the base plate.
- Elastic (vector) method for the perimeter fillet weld.
- ACI 318 simplified single-anchor breakout/pullout checks — for a real
  anchor **group**, group effects (ANc vs ANco, edge/spacing modifiers per
  anchor) should be checked per ACI 318 Chapter 17 rather than only the
  simplified single-anchor form used here.
- This tool supports preliminary design/checking. A licensed engineer
  should verify governing code edition, load combinations, and anchor
  group effects before construction use.
