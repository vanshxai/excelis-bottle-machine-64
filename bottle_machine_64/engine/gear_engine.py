"""
Series gear-train touch engine.

Given a chain of shafts (each with an input wheel meshing the previous shaft and an output wheel
meshing the next), it answers: "if a tangential force F is applied to wheel W on shaft K, how much extra
current does the motor draw?" The load torque is carried back up the chain through every mesh
(divided by the mesh's speed ratio and efficiency), then turned into current with the motor's torque
constant. Every number is computed through the project's formula stock via runtime.apply(), which
refuses to run with a missing value; nothing is defaulted.

Validated against the 150 RPM gear rig's measured part-interruption bands: see ../validation/.
"""
import json
import os
import tempfile

import formula_pack
import runtime


def use_stock(directory=None):
    """Point runtime.apply at a formula stock built from the core engine (+ the local gear formulas)."""
    directory = directory or tempfile.mkdtemp(prefix="gear_engine_")
    with open(os.path.join(directory, "formulas_stock.json"), "w") as f:
        json.dump(formula_pack.build_stock(), f)
    runtime._STOCK_CACHE.pop(directory, None)
    runtime.set_project(directory)
    return directory


class GearTrain:
    """shafts: list of {"name", "in": teeth meshing the previous shaft (None for the motor shaft),
    "out": teeth meshing the next shaft (None for the last shaft)}; module_mm: gear module."""

    def __init__(self, shafts, module_mm, mesh_eta):
        self.shafts, self.module_mm, self.eta = shafts, module_mm, mesh_eta

    # --- geometry -------------------------------------------------------------------------
    def radius_m(self, teeth):
        Dp = runtime.apply("gear_module", "Dp_gear", m_gear=self.module_mm / 1000.0, Np_gear=float(teeth))
        return Dp / 2.0

    def mesh_ratio(self, j):
        """Speed ratio of the mesh between shaft j-1 and shaft j: how many times faster the driver turns."""
        return self.shafts[j]["in"] / self.shafts[j - 1]["out"]

    def motor_speed_rad_s(self, omega_last):
        w = omega_last
        for j in range(len(self.shafts) - 1, 0, -1):
            w = w * self.mesh_ratio(j)
        return w

    # --- the touch -> motor-torque -> current chain -----------------------------------------
    def motor_torque(self, shaft_index, wheel_teeth, F_tangential):
        T = runtime.apply("lever_torque", "T_lever", F_tan=F_tangential, r_arm=self.radius_m(wheel_teeth))
        for j in range(shaft_index, 0, -1):
            T = runtime.apply("gear_reflected_torque", "T_in", T_out=T, GR=self.mesh_ratio(j), eta=self.eta)
        return T

    def delta_current(self, shaft_index, wheel_teeth, F_tangential, Kt):
        return runtime.apply("torque", "I", T=self.motor_torque(shaft_index, wheel_teeth, F_tangential), Kt=Kt)


def motor_constants(V_supply, I_noload, R_armature, omega_motor):
    """Back-EMF constant from the motor's own running state: V = I*R + Ke*omega  ->  Ke = (V - I*R)/omega.
    Kt = Ke for a DC motor in SI units (a stated assumption, not a measurement)."""
    Ke = runtime.apply("angular_velocity", "Ke", omega=omega_motor, I=I_noload, R=R_armature, V=V_supply)
    return {"Ke": Ke, "Kt": Ke}
