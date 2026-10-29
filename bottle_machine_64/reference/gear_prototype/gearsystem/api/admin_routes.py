"""Admin / AI-chat routes -- unrelated to gearbox physics. Relocated from
gearsystem150_app.py (_load_openai_key_from_file, api_admin_company_info,
api_admin_ask_ai, _gearsystem_fault_machine_state).

_gearsystem_fault_machine_state() reads live detection + calibration
state to feed the AI's fault_check mode -- it lives here rather than in
detection_routes.py since this route is its only consumer."""
import json
import os

from flask import Blueprint, jsonify, request

from .. import PROJECT_ROOT
from ..calibration import search
from ..detection import live_state
from ..twin import store as twin_store

bp = Blueprint("gearsystem_admin", __name__)

COMPANY_INFO_PATH = os.path.join(PROJECT_ROOT, "company_info.txt")
_OPENAI_KEY_PATH = os.path.join(PROJECT_ROOT, "openai.key")


def _load_openai_key_from_file():
    if os.path.exists(_OPENAI_KEY_PATH):
        with open(_OPENAI_KEY_PATH) as f:
            return f.read().strip() or None
    return None


@bp.route("/api/admin/company_info", methods=["GET", "POST"])
def api_admin_company_info():
    if request.method == "POST":
        text = (request.get_json(silent=True) or {}).get("text", "")
        with open(COMPANY_INFO_PATH, "w") as f:
            f.write(text)
        return jsonify({"ok": True})
    text = ""
    if os.path.exists(COMPANY_INFO_PATH):
        with open(COMPANY_INFO_PATH) as f:
            text = f.read()
    return jsonify({"text": text})


def _gearsystem_fault_machine_state():
    """Real computed state of the verified metal-twin, for the AI to
    interpret -- reuses the exact same live-current + implied-force logic
    as api_gearsystem_roulette_metal_guesses, just against the confirmed
    twin instead of an unverified card batch."""
    verified = twin_store.load_verified()
    if verified is None:
        return None, ("No verified gearbox yet -- run a roulette round on "
                       "/twin/gearsystem150/roulette and verify a card first, then try again.")

    with live_state.lock:
        live_val = live_state.state["current_A"]

    if live_state.real_zero_A is None:
        return {
            "verified_signatures": verified["signatures"],
            "I_baseline_A": verified["I_baseline_A"],
            "detected": "not_calibrated",
        }, None

    if live_val is None:
        return {
            "verified_signatures": verified["signatures"],
            "I_baseline_A": verified["I_baseline_A"],
            "detected": "no_live_reading",
        }, None

    real_delta = live_val - live_state.real_zero_A
    noise_floor = live_state.noise_floor_at_cal or live_state.NOISE_FLOOR_MIN

    if abs(real_delta) < noise_floor:
        detected = "no_touch"
    else:
        card = dict(verified)
        card["valid"] = True
        guess = search.guess_for_card(card, real_delta)
        detected = guess if guess else "implausible"

    return {
        "verified_signatures": verified["signatures"],
        "I_baseline_A": verified["I_baseline_A"],
        "live_real_delta_A": round(real_delta, 6),
        "noise_floor_A": round(noise_floor, 6),
        "detected": detected,
    }, None


@bp.route("/api/admin/ask_ai", methods=["POST"])
def api_admin_ask_ai():
    api_key = os.environ.get("OPENAI_API_KEY") or _load_openai_key_from_file()
    if not api_key:
        return jsonify({"error": "OpenAI is not configured. Set the OPENAI_API_KEY environment variable."}), 200
    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "chat")
    question = body.get("question", "").strip()

    machine_state = None
    if mode == "fault_check":
        machine_state, error = _gearsystem_fault_machine_state()
        if error:
            return jsonify({"answer": error})
        question = question or "Analyze the current machine state and report any detected or likely faults."
    elif not question:
        return jsonify({"error": "No question provided."}), 400

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        formula_db = ""
        formula_db_path = os.path.join(PROJECT_ROOT, "FORMULA_DATABASE.md")
        if os.path.exists(formula_db_path):
            with open(formula_db_path) as f:
                formula_db = f.read()

        company_info = ""
        if os.path.exists(COMPANY_INFO_PATH):
            with open(COMPANY_INFO_PATH) as f:
                company_info = f.read()

        system_parts = [
            "You are an assistant and fault-detection analyst for a 150 RPM metal gearbox digital twin.",
            "Full formula database (source of truth for all physics):\n" + formula_db,
        ]
        if company_info.strip():
            system_parts.append("Additional information provided by the company:\n" + company_info)
        if machine_state is not None:
            system_parts.append(
                "Computed current machine state (real sensor + verified twin data -- "
                "use this, don't invent numbers):\n" + json.dumps(machine_state, indent=2)
            )
            system_parts.append(
                "Task: act as a fault-detection analyst. Explain what the computed state implies, "
                "flag any likely fault or touch event, note your confidence, and explain your reasoning "
                "in plain language."
            )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "\n\n".join(system_parts)},
                {"role": "user", "content": question},
            ],
        )
        answer = resp.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 200
