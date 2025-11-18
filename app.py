import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

RESROBOT_TRIP_URL = "https://api.resrobot.se/v2.1/trip"


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def pretty_mode_and_operator(
    product: Dict[str, Any], operators: List[Dict[str, Any]]
) -> Tuple[str, str, str]:
    """
    Returns (mode_label, operator_label, line_name).

    mode_label examples:
    - Tunnelbana (SL)
    - Pendeltåg (SL)
    - Tåg (Mälartåg)
    - Buss (UL)
    - fallback: Kollektivtrafik
    """

    product = product or {}
    line_name = str(product.get("name") or "")
    base_name = line_name.lower()
    category = str(product.get("catOut") or product.get("catIn") or "").lower()

    operator_label = ""
    for operator in operators:
        if not isinstance(operator, dict):
            continue
        name = operator.get("name")
        if name:
            operator_label = str(name)
            break

    if "t-bana" in base_name or "tunnelbana" in base_name or "subway" in category:
        mode_label = "Tunnelbana"
    elif "pendeltåg" in base_name:
        mode_label = "Pendeltåg"
    elif "mälartåg" in base_name:
        mode_label = "Tåg (Mälartåg)"
    elif "tåg" in base_name or "train" in category:
        mode_label = "Tåg"
    elif "buss" in base_name or "bus" in category:
        mode_label = "Buss"
    else:
        mode_label = "Kollektivtrafik"

    if operator_label:
        if "mälartåg" in base_name:
            pass
        elif operator_label in {"SL", "UL"} and operator_label not in mode_label:
            mode_label = f"{mode_label} ({operator_label})"
        elif operator_label not in mode_label:
            mode_label = f"{mode_label} ({operator_label})"

    return mode_label, operator_label, line_name


def _parse_trip(trip: Dict[str, Any]) -> Dict[str, Any]:
    legs = _ensure_list(trip.get("LegList", {}).get("Leg"))
    if not legs:
        raise ValueError("ResRobot response is missing leg information.")

    first_leg = legs[0]
    last_leg = legs[-1]

    def _leg_time(leg_part: Dict[str, Any]) -> datetime:
        date_str = leg_part.get("date")
        time_str = leg_part.get("time")
        if not date_str or not time_str:
            raise ValueError("Missing date/time information on a leg.")
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

    departure_dt = _leg_time(first_leg.get("Origin", {}))
    arrival_dt = _leg_time(last_leg.get("Destination", {}))
    total_minutes = int((arrival_dt - departure_dt).total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)

    simplified_legs = []
    for leg in legs:
        origin = leg.get("Origin", {})
        destination = leg.get("Destination", {})
        products = _ensure_list(leg.get("Product"))
        product = products[0] if products else {}
        operators = _ensure_list(leg.get("Operator"))
        mode_label, operator_label, line_name = pretty_mode_and_operator(product, operators)
        mode = leg.get("type") or leg.get("name") or mode_label
        simplified_legs.append(
            {
                "mode": mode,
                "modeLabel": mode_label,
                "operator": operator_label,
                "lineName": line_name,
                "origin": origin.get("name"),
                "destination": destination.get("name"),
                "departure": origin.get("time"),
                "arrival": destination.get("time"),
                "description": f"{mode_label}: {origin.get('name')} → {destination.get('name')}",
            }
        )

    return {
        "departureTime": departure_dt.strftime("%H:%M"),
        "arrivalTime": arrival_dt.strftime("%H:%M"),
        "totalTravelTime": f"{hours}h {minutes:02d}m",
        "legs": simplified_legs,
    }


def simplify_trip(trip: Dict[str, Any]) -> Dict[str, Any]:
    """Simplify a raw ResRobot trip and add summary metadata."""
    result = _parse_trip(trip)
    legs = result.get("legs") or []
    vehicle_legs = [
        leg
        for leg in legs
        if not str(leg.get("modeLabel") or "").lower().startswith("gång")
        and not str(leg.get("modeLabel") or "").lower().startswith("gång (byte)")
    ]
    num_changes = max(len(vehicle_legs) - 1, 0)
    modes: List[str] = []
    for leg in legs:
        mode_label = leg.get("modeLabel")
        if mode_label and mode_label not in modes:
            modes.append(mode_label)
    result["numChanges"] = num_changes
    result["modes"] = modes
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/trip")
def trip():
    origin_id = request.args.get("originId")
    dest_id = request.args.get("destId")
    date = request.args.get("date")
    time = request.args.get("time")

    if not all([origin_id, dest_id, date, time]):
        return jsonify({"error": "originId, destId, date och time måste anges."}), 400

    api_key = os.getenv("RESROBOT_API_KEY")
    if not api_key:
        return jsonify({"error": "RESROBOT_API_KEY saknas på servern."}), 500

    try:
        response = requests.get(
            RESROBOT_TRIP_URL,
            params={
                "accessId": api_key,
                "originId": origin_id,
                "destId": dest_id,
                "date": date,
                "time": time,
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({"error": f"Kunde inte hämta resa: {exc}"}), 502

    data = response.json()
    raw_trips = _ensure_list(data.get("Trip"))
    if not raw_trips:
        return jsonify({"error": "Ingen resa hittades för den här sökningen."}), 404

    try:
        simplified_trips = [simplify_trip(trip) for trip in raw_trips]
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"trips": simplified_trips})


if __name__ == "__main__":
    app.run(debug=True)
