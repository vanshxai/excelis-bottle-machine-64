"""Disturbance Model -- STUB in the sense that formulas_database.json's
documented disturb_1 (Tdisturb = ktouch * P, a 0-10 pressure metric) and
combine_1 (summing per-stage reflected torque back to the motor shaft)
both have "implemented_in": null -- neither is coded as written.

What IS implemented (in signature/dynamic.py, calling
gear_train.mesh_torque/derivatives) is a different but related thing: a
touch is injected directly as a torque or angular impulse at the touched
node (force_n / impulse_ns, converted via the gear's own pitch radius),
not via a 0-10 pressure metric run through ktouch. This file exists as
the named home for the documented pressure-based model if a later phase
implements it; it does not currently wrap anything, so there is nothing
to relocate into it yet.
"""

# Placeholder for when/if a later phase implements disturb_1 as documented.
K_TOUCH = None
