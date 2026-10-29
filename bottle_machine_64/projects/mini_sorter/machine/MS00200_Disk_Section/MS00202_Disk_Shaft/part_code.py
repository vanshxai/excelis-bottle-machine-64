"""Generated for MS00202 (Disk Shaft) - type: Shaft, role: active.
Drive chain, this part to the motor: MS00202 -> MS00201.
Every value is either measured from the STEP file or typed in by the user; nothing is assumed."""
from runtime import apply

MU = 0.002  # dimensionless - typed in by the user
R_SELF = 0.007971  # m - measured from the STEP file (MS00202, round part)
R_MS00202 = 0.007971  # m - measured from the STEP file (MS00202, round part)


def motor_torque(effort):
    """Extra torque (N*m) the motor must supply when `effort` (N) is applied at this part."""
    q = apply('bearing_friction_torque', 'Tf', F=effort, mu=MU, r=R_SELF)  # torque at the shaft's bearings
    # MS00202 turns with MS00201 (same shaft): torque passes through unchanged
    return q  # N*m at the motor's output shaft
