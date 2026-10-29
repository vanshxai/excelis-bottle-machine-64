"""
The formula "stock" a machine project is built from.

Core formulas are copied (as text) out of the core engine into the project at build time, so a
finished project is self-contained. A small number of textbook relations the core engine does not
have yet are listed as LOCAL with their status, so nothing is hidden.
"""
import os
import sys

CORE_DIR_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "faulter-formula-brain")

CORE_NAMES = ["torque", "bearing_friction_torque", "disc_brake_torque", "angular_velocity", "gear_module"]

LOCAL = {
    "lever_torque": {
        "equation": "T_lever = F_tan*r_arm",
        "domain": "mechanical",
        "origin": "local",
        "status": "textbook definition of torque (force times perpendicular lever arm); "
                  "citation still to be fetched and the formula added to the core engine",
    },
    "gear_reflected_torque": {
        "equation": "T_in = T_out/(GR*eta)",
        "domain": "mechanical_drives",
        "origin": "local",
        "status": "torque a driving shaft must supply to deliver T_out through one gear mesh with speed "
                  "ratio GR (driver turns GR times faster than the driven shaft) and efficiency eta. "
                  "Follows from core 'efficiency' (eta = P_out/P_in) and 'power_mechanical' (P = T*omega) "
                  "with omega_in = GR*omega_out; citation still to be fetched and the formula added to the core engine",
    },
}


def build_stock(core_dir=None):
    core_dir = core_dir or os.environ.get("FAULTER_CORE_DIR", CORE_DIR_DEFAULT)
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import formulas as core  # the core engine's formula table
    stock = {}
    for name in CORE_NAMES:
        eq = core.FORMULAS[name]
        stock[name] = {"equation": f"{eq.lhs} = {eq.rhs}", "domain": core.FORMULA_DOMAINS.get(name, ""),
                       "origin": "core engine"}
    stock.update(LOCAL)
    return stock
