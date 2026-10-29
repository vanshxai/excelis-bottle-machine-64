"""Current Model -- the mechanical-to-electrical conversion, and its
force-domain inverse.

torque_to_current() is the ONE conversion point that existed 5 times
verbatim before this refactor: twice in gear_train.run_formula_chain(),
twice in gear_train.run_formula_chain_capless(), and once in
signature/dynamic.py's RK4 loop (formerly dynamic_gear_simulator.py line
430). Collapsed here without changing its value -- see the migration
plan's "duplicated logic to merge" section.

FORCE_REFERENCE_N and rank_candidates_by_force_fit() hold the first 1-2
steps that used to be independently copy-pasted in
calibration/search.py's guess_for_card() and detection/matching.py's
_ina228_gear_matches(): compute each gear's implied touch force from an
observed current delta, and keep only the physically plausible ones. Each
caller still does its OWN rounding/sorting/final-selection on top --
their rounding order differs (one rounds before sorting, one after), so
that part is deliberately NOT merged, to keep both callers' output
byte-identical to before the refactor.

This module lives in physics/ rather than detection/ specifically so that
calibration/ (which needs the same ranking logic, at search/guess time,
before anything is verified) does not have to import from detection/ --
see the refactor plan's "key interpretive decisions" #3.
"""

FORCE_REFERENCE_N = 2.0  # relocated from gearsystem_roulette_metal.py, unchanged


def torque_to_current(delta_torque_nm, current_per_nm, i_baseline=0.0):
    """delta_I = delta_torque * CURRENT_PER_NM (+ optional baseline).
    The one mechanical->electrical conversion in the whole codebase."""
    return i_baseline + delta_torque_nm * current_per_nm


def implied_force_n(delta_a, sensitivity_a_per_n):
    """Algebraic inverse: given an observed current delta and a gear's
    delta_I_per_N_A sensitivity, back out the touch force that would
    explain it."""
    return abs(delta_a) / sensitivity_a_per_n


def rank_candidates_by_force_fit(delta_a, signatures, force_min_n, force_max_n):
    """For each signature, compute the touch force implied by delta_a and
    keep only physically plausible candidates (within [force_min_n,
    force_max_n]). Returns unrounded, unsorted candidates in signature
    order -- each caller applies its own existing sort/rounding/selection
    on top (see module docstring for why that part isn't shared)."""
    candidates = []
    for sig in signatures:
        sens = sig.get("delta_I_per_N_A")
        if not sens:
            continue
        force_n = implied_force_n(delta_a, sens)
        if force_min_n <= force_n <= force_max_n:
            candidates.append({
                "touch_point_id": sig["touch_point_id"],
                "component": sig["name"],
                "implied_force_N": force_n,
            })
    return candidates
