"""Steady-State Signature -- thin wrapper over physics/gear_train.py's
fast, quasi-static signature computation (RPM chain -> mesh frequency ->
baseline current -> per-gear delta-I signature -> rise time). Returns the
exact same dict shape as gear_train.run_formula_chain[_capless] -- this
layer adds naming/orchestration, not new computation, per the migration
plan's "thin wrapper" decision for Physics/Signature.

This is the FAST signature path (a single dict multiply/divide chain, no
integration) -- the one calibration/search.py's candidate sweep calls
thousands of times per round. signature/dynamic.py's RK4 path is the slow
one, deliberately run only once, at verify time.
"""
from ..physics import gear_train


def generate_steady_signature(constants):
    """All 4 touch points' steady-force + impact-response signatures for
    one twin, anchored on the (possibly stale, see out-of-scope notes)
    capped 150 RPM Output assumption."""
    return gear_train.run_formula_chain(constants)


def generate_steady_signature_capless(constants, rpm_yellow):
    """Same as generate_steady_signature, re-anchored on a measured
    rpm_yellow instead of the (currently invalid) capped Output speed."""
    return gear_train.run_formula_chain_capless(constants, rpm_yellow)
