"""Page routes -- thin render_template_string() wrappers, unchanged from
gearsystem150_app.py. Templates themselves live in templates.py."""
from flask import Blueprint, redirect, render_template_string

from . import templates

bp = Blueprint("gearsystem_pages", __name__)


@bp.route("/twin/gearsystem150/roulette")
def gearsystem150_roulette_page():
    return render_template_string(templates.GEARSYSTEM_ROULETTE_TEMPLATE, section="gearsystem150", rig="metal",
                                   rig_name="150 RPM Gear System -- prototype, 4 touchable gears "
                                             "(Yellow / Blue / Green / Red), motor collapsed to one constant",
                                   api_base="/api/gearsystem/roulette_metal")


@bp.route("/twin/gearsystem150")
def gearsystem150_page():
    return render_template_string(templates.GEARSYSTEM150_TEMPLATE, section="gearsystem150")


@bp.route("/twin/gearsystem150/twins")
def gearsystem150_twins_page():
    return render_template_string(templates.GEARSYSTEM_TWIN_BATCH_TEMPLATE)


@bp.route("/twin/gearsystem150/touch-sim")
def gearsystem150_touch_sim_page():
    return render_template_string(templates.GEARSYSTEM_TOUCH_SIM_TEMPLATE)


@bp.route("/twin/gearsystem150/live-model")
def gearsystem150_live_model_page():
    return render_template_string(templates.GEARSYSTEM_LIVE_MODEL_TEMPLATE)


@bp.route("/twin/gearsystem150/motor")
def gearsystem150_motor_page():
    return render_template_string(templates.GEARSYSTEM_MOTOR_TEMPLATE)


@bp.route("/twin/gearsystem150/raw")
def gearsystem150_raw_page():
    return render_template_string(templates.GEARSYSTEM_RAW_TEMPLATE)


@bp.route("/twin/gearsystem150/validate")
def gearsystem150_validate_page():
    return render_template_string(templates.GEARSYSTEM_VALIDATE_TEMPLATE)


@bp.route("/")
def index():
    return redirect("/twin/gearsystem150")
