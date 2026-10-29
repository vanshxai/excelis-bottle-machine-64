"""150 RPM Gear System -- standalone digital-twin web app.

Independent from the main YANTHROS platform: owns its own Flask process
and port. Has a live current-signature data-collection gateway (see
gearsystem/detection/acquisition.py) that scans local serial ports for
an ESP32-class sensor and publishes whatever it reports straight to the
HUD.

As of the Phase-1 architecture refactor, this file is just the app
factory: it creates the Flask app and registers blueprints from
gearsystem/api/*. All actual logic lives in the gearsystem/ package,
organized into layers (twin/, calibration/, physics/, signature/,
detection/, api/) -- see gearsystem/__init__.py and the migration plan
(/Users/mac/.claude/plans/snug-cuddling-teacup.md) for the full
rationale. formula_chain_metal.py, gearsystem_roulette_metal.py,
dynamic_gear_simulator.py, and constraint_sampling.py still exist at this
same top-level location as thin re-export shims, in case anything outside
this app imports them directly -- see those files' own docstrings.

FORMULA_DATABASE.md remains the full formula reference.
"""
from flask import Flask

from gearsystem.api import (
    admin_routes,
    calibration_routes,
    detection_routes,
    pages,
    signature_routes,
    twin_routes,
)
from gearsystem.detection.acquisition import start_gearsystem_sensor_gateway

app = Flask(__name__)
app.register_blueprint(twin_routes.bp)
app.register_blueprint(calibration_routes.bp)
app.register_blueprint(signature_routes.bp)
app.register_blueprint(detection_routes.bp)
app.register_blueprint(admin_routes.bp)
app.register_blueprint(pages.bp)


if __name__ == "__main__":
    start_gearsystem_sensor_gateway()
    app.run(host="0.0.0.0", port=5053, debug=True, use_reloader=False, threaded=True)
