"""Motor Model -- Phase-1 scope is small: the one standalone motor-body
quantity that's actually computed today, the rotor's own rotational
inertia (added onto Yellow's node inertia in gear_train.build_gear_train,
since the rotor is a separate physical mass rigidly on the same shaft as
Yellow's pinion gear).

The real motor electrical model (V=iR+L di/dt+Ke*omega, T=Kt*i, shaft
balance -- motor_1/2/3 in formulas_database.json) is NOT implemented here
or anywhere else in this codebase -- see physics/electrical.py."""
import math


def motor_rotor_inertia_kgm2(c):
    """The motor's own armature/rotor -- a separate physical cylinder
    rigidly on the same shaft as Yellow's pinion gear, not the pinion
    itself. MOTOR_ROTOR_RADIUS_MM/MOTOR_ROTOR_LENGTH_MM are assumed
    typical small-can-motor dimensions (not measured), and reuse the
    gears' own MATERIAL_DENSITY_KG_M3 as a stand-in for rotor material
    (also not given) -- see constraint_registry_metal.json's
    geometry_and_material_note. Relocated from
    dynamic_gear_simulator.py::_motor_rotor_inertia_kgm2, unchanged."""
    r_m = c["MOTOR_ROTOR_RADIUS_MM"] / 1000
    L_m = c["MOTOR_ROTOR_LENGTH_MM"] / 1000
    mass_kg = c["MATERIAL_DENSITY_KG_M3"] * math.pi * (r_m ** 2) * L_m
    return 0.5 * mass_kg * (r_m ** 2)
