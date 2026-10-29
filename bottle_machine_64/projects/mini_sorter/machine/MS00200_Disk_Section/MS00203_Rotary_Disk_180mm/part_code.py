"""Generated for MS00203 (Rotary Disk, 180mm) - type: Rotating disk, role: passive.
Drive chain, this part to the motor: MS00203 -> MS00202 -> MS00201.
Every value is either measured from the STEP file or typed in by the user; nothing is assumed."""
from runtime import apply

MU = 0.3  # dimensionless - typed in by the user
R_SELF = 0.08996299999999999  # m - measured from the STEP file (MS00203, round part)
R_MS00203 = 0.08996299999999999  # m - measured from the STEP file (MS00203, round part)
R_MS00202 = 0.007971  # m - measured from the STEP file (MS00202, round part)


def motor_torque(effort):
    """Extra torque (N*m) the motor must supply when `effort` (N) is applied at this part."""
    q = apply('disc_brake_torque', 'T_brake', F_brake=effort, R_brake=R_SELF, mu_brake=MU)  # drag torque at the disk rim
    # MS00203 turns with MS00202 (same shaft): torque passes through unchanged
    # MS00202 turns with MS00201 (same shaft): torque passes through unchanged
    return q  # N*m at the motor's output shaft
