"""Twin routes -- placeholder. No dedicated /api/gearsystem/twin/* routes
exist yet; twin data is currently exposed only as part of
signature_routes.py (motor_chain) and calibration_routes.py
(roulette_metal/verified). Kept as an empty blueprint so a future phase
has a named home for dedicated twin endpoints without another
restructuring pass."""
from flask import Blueprint

bp = Blueprint("gearsystem_twin", __name__)
