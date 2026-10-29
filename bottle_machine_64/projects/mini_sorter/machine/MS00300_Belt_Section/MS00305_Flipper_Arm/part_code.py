"""Generated for MS00305 (Flipper Arm) - type: Flipper arm, role: passive.
Drive chain, this part to the motor: MS00305 -> MS00304 -> MS00302 -> MS00301.
Every value is either measured from the STEP file or typed in by the user; nothing is assumed."""
from runtime import apply

R_MS00302 = 0.021962  # m - measured from the STEP file (MS00302, round part)


def motor_torque(effort):
    """Extra torque (N*m) the motor must supply when `effort` (N) is applied at this part."""
    q = effort  # force acting along the belt (N)
    # MS00305 pushes directly on MS00304: force passes through unchanged
    q = apply('lever_torque', 'T_lever', F_tan=q, r_arm=R_MS00302)  # belt force becomes torque on MS00302
    # MS00302 turns with MS00301 (same shaft): torque passes through unchanged
    return q  # N*m at the motor's output shaft
