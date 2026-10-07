"""
End-to-end verification for chatbot 3D navigation ("fly to <anywhere>").
Hits the live /api/chat endpoint and checks intent, action payload, coordinates,
and that no unrelated RAG document leaks into the reply.
"""

import json
import sys
import urllib.request

BASE_URL = "http://localhost:8050/api/chat"

# (message, expected action type, expected approx (lat, lon) or None, tolerance deg)
TESTS = [
    ("fly to newyork", "fly_to_coords", (40.71, -74.00), 1.0),
    ("Fly to New York City please!", "fly_to_coords", (40.71, -74.00), 1.0),
    ("take me to Tokyo", "fly_to_coords", (35.68, 139.76), 1.0),
    ("zoom in on paris", "fly_to_coords", (48.85, 2.35), 1.0),
    ("fly to mexico city", "fly_to_coords", (19.43, -99.13), 1.0),
    ("amake sylhet nie jao", "fly_to_coords", (24.8, 91.8), 1.0),
    ("নিউ ইয়র্কে নিয়ে যাও", "fly_to_coords", (40.71, -74.00), 1.0),
    ("fly to the amazon", "fly_to_preset", (-3.46, -62.21), 0.1),
    ("fly to bangladesh", "fly_to_preset", (23.85, 90.35), 0.1),
    ("fly to 40.71, -74.00", "fly_to_coords", (40.71, -74.00), 0.05),
    ("fly to xqzvplorkt", None, None, 0),  # unresolvable -> friendly message, no action
]


def post(message):
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps({"message": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    passed = failed = 0
    for msg, exp_type, exp_ll, tol in TESTS:
        try:
            d = post(msg)
            action = d.get("action") or {}
            params = action.get("params") or {}
            ok = d.get("intent") == "action" and action.get("type") == exp_type if exp_type else (
                d.get("intent") == "action" and not d.get("action")
            )
            if ok and exp_ll:
                ok = abs(params.get("lat", 999) - exp_ll[0]) <= tol and abs(params.get("lon", 999) - exp_ll[1]) <= tol
            # Reply must never be an unrelated knowledge-base dump
            if "Bangladesh Wildfire and Agricultural Fire Analysis" in d.get("answer", "") or d.get("sources"):
                ok = False
            status = "PASS" if ok else "FAIL"
            passed += ok
            failed += not ok
            print(f"[{status}] {msg!r}")
            print(f"        intent={d.get('intent')} action={action.get('type')} "
                  f"lat={params.get('lat')} lon={params.get('lon')} alt={params.get('alt')}")
            print(f"        answer: {d.get('answer', '').splitlines()[0][:110]}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] {msg!r}: {e}")
    print(f"\nSummary: {passed} passed, {failed} failed out of {len(TESTS)}")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
