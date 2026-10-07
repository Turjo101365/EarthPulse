"""
Lightweight Intent Router & Action Dispatcher for EarthPulse
Routes queries between RAG (documentation), Live Telemetry (spatial index / FIRMS),
ML Spread Prediction (XGBoost), and 3D Action Execution (Cesium camera fly-to).
"""

import re
import unicodedata
from typing import Dict, Any, Optional, Tuple

from .geocoding_service import geocoding_service

# Known geographic presets mapping to Cesium 3D camera targets
LOCATION_PRESETS = {
    "bangladesh": {"name": "Bangladesh", "lat": 23.85, "lon": 90.35, "alt": 750000, "preset": "bangladesh"},
    "dhaka": {"name": "Dhaka Metro", "lat": 23.81, "lon": 90.41, "alt": 85000, "preset": "dhaka"},
    "chittagong": {"name": "Chittagong Hill Tracts", "lat": 22.35, "lon": 92.18, "alt": 110000, "preset": "chittagong"},
    "sundarbans": {"name": "Sundarbans Mangrove", "lat": 22.15, "lon": 89.60, "alt": 95000, "preset": "sundarbans"},
    "california": {"name": "California", "lat": 36.77, "lon": -119.41, "alt": 950000, "preset": "california"},
    "amazon": {"name": "Amazon Basin", "lat": -3.46, "lon": -62.21, "alt": 1800000, "preset": "amazon"},
    "pantanal": {"name": "Pantanal Wetlands", "lat": -17.50, "lon": -57.00, "alt": 850000, "preset": "pantanal"},
    "india": {"name": "India", "lat": 20.59, "lon": 78.96, "alt": 3200000, "preset": "india"},
    "china": {"name": "China", "lat": 35.86, "lon": 104.19, "alt": 3800000, "preset": "china"},
    "australia": {"name": "Australia", "lat": -25.27, "lon": 133.77, "alt": 3500000, "preset": "australia"},
    "greece": {"name": "Greece Arc", "lat": 39.07, "lon": 21.82, "alt": 750000, "preset": "greece"},
    "spain": {"name": "Spain", "lat": 40.46, "lon": -3.74, "alt": 900000, "preset": "spain"},
    "congo": {"name": "Congo Basin", "lat": -4.03, "lon": 21.75, "alt": 1800000, "preset": "congo"},
    "canada": {"name": "Canada", "lat": 56.13, "lon": -106.34, "alt": 4200000, "preset": "canada"},
}


class IntentRouter:
    def classify_intent(self, query: str) -> str:
        """
        Classifies query into: 'rag', 'live_data', 'ml_prediction', 'action', or 'hybrid'.
        """
        q = query.lower().strip()

        # 0. Conversational, Capability, Language, Greeting & Feedback Check
        conv_triggers = [
            "bangla bolte paro", "bangla jano", "speak bengali", "speak bangla", "tumi ki bangla",
            "tumi ke", "who are you", "what can you do", "ki korte paro", "kivabe use korbo",
            "kibhabe use korbo", "help me", "how to use", "thikmoto answer", "user friendly na",
            "kemon acho", "kemon achen", "assalamu alaikum", "bolsi je",
            "kothopokothon", "knowledgebase thekei", "knowledge base theke", "always je knowledgebase"
        ]
        if any(t in q for t in conv_triggers) or bool(re.search(r"\b(hi|hey|hello|greetings)\b", q)) or (
            ("bangla" in q or "bengali" in q) and any(w in q for w in ["bol", "par", "jan", "kotha", "speak", "understand", "likh", "bujh"])
        ) or (
            any(w in q for w in ["answer", "chatbot", "uttor", "kothopokothon"]) and 
            any(w in q for w in ["thik", "friendly", "baje", "diche na", "problem", "kharaf", "jacche na", "bujhe na", "somossha"])
        ) or (
            ("knowledgebase" in q or "knowledge base" in q) and any(w in q for w in ["theke", "always", "shob", "sob", "shudu", "shudhu", "only"])
        ) or (
            bool(re.search(r"\b(tumi|tuti|apni)\b", q)) and bool(re.search(r"\b(ke|ki|kemon|kotha|bol)\b", q))
        ):
            return "conversational"

        # 1. Web Search Check (Explicit or news/external search queries)
        web_search_triggers = [
            "search web", "search the web", "web search", "google search", "search internet",
            "search google", "web e search", "online e search", "google e khujo", "web theke",
            "latest news", "breaking news", "recent news", "today's news", "shomporke khobor",
            "khobor ki", "news ki", "recent updates", "current news", "online e dekho", "internet theke",
            "web search koro", "web e khujo"
        ]
        if any(t in q for t in web_search_triggers) or (
            ("search" in q or "খোঁজ" in q or "খবর" in q or "news" in q) and 
            any(w in q for w in ["web", "internet", "google", "online", "latest", "recent", "breaking", "ajker", "বর্তমান", "khobor"])
        ):
            return "web_search"

        # 2. Action Check (Explicit 3D navigation commands)
        if self.extract_destination(query) and not any(
            w in q for w in ["what", "how", "why", "explain", "কী", "কেন", "ব্যাখ্যা"]
        ):
            return "action"

        if any(w in q for w in ["run scenario", "trigger scenario", "crisis scenario", "সিনেরিও"]):
            return "action"

        # 2. ML Prediction Check (Spread, Risk probability for coordinates)
        ml_predict_triggers = [
            "predict spread", "forecast spread", "prediction for coordinate", "fire risk prediction",
            "predicted fire risk", "predicted risk", "spread risk", "risk for coordinate",
            "spread probability", "fire propagation", "how will the fire spread", "কতটুকু ছড়াবে", "ছড়ানোর ঝুঁকি"
        ]
        if any(t in q for t in ml_predict_triggers) or (
            ("predict" in q or "forecast" in q or "পূর্বাভাস" in q) and 
            ("risk" in q or "spread" in q or "coordinate" in q or "ঝুঁকি" in q)
        ):
            return "ml_prediction"

        # 3. Live Data Telemetry Check
        live_triggers = [
            "current number of hotspots", "hotspots shown on the map", "today's bangladesh hotspot",
            "current hotspot count", "how many fires are detected today", "highest frp right now",
            "peak fire right now", "current global summary", "how many fires today", "active hotspots right now",
            "hotspot count", "এখন কয়টা আগুন", "বর্তমান হটস্পট সংখ্যা", "আজকের হটস্পট", "সর্বোচ্চ আগুন কত",
            "kono agun ache", "agun ache", "koyta agun", "aguner obostha", "fire ache", "any fires",
            "fires in bangladesh", "shobcheye boro agun", "boro agun kothay", "agun kothay"
        ]
        if any(t in q for t in live_triggers):
            return "live_data"

        # Regional queries asking about current status in Bangladesh/areas
        if any(w in q for w in ["in bangladesh right now", "current status in", "বর্তমান অবস্থা", "bangladesh e", "বাংলাদেশে"]):
            if any(w in q for w in ["fire", "hotspot", "agun", "আগুন", "status", "obostha", "অবস্থা", "koyta", "কয়টা"]):
                return "live_data"

        # 4. Hybrid Queries (e.g. comparing sensors AND asking about current stats)
        if ("compare" in q or "difference" in q or "পার্থক্য" in q) and any(w in q for w in ["now", "current", "today", "এখন"]):
            return "hybrid"

        # 5. Default to RAG for technical / conceptual questions
        return "rag"

    # English: "fly to X", "take me to X", "zoom in on X", "show me X on the globe"
    _EN_NAV = re.compile(
        r"\b(?:fly|take\s+me|navigate|go|jump|travel|teleport|zoom(?:\s+in)?|center|centre)"
        r"\s+(?:over\s+|on\s+|in\s+on\s+|the\s+camera\s+)?(?:to|over|on|into)\s+(?:the\s+)?(.+)",
        re.IGNORECASE,
    )
    # Banglish: "newyork e niye jao", "amake sylhet nie jao", "paris e jao"
    _BANGLISH_NAV = re.compile(
        r"^(?:amake\s+|amader\s+|ektu\s+)?(.+?)\s*(?:\b(?:e|te|a|y)\b\s*)?"
        r"\b(?:niye|nie|niya)\s+(?:jao|cholo|chalo|jaw)\b|^(?:amake\s+)?(.+?)\s+(?:e|te)\s+jao\b",
        re.IGNORECASE,
    )
    # Bengali script: "নিউ ইয়র্কে নিয়ে যাও"
    _BN_NAV = re.compile(unicodedata.normalize("NFC", r"^(?:আমাকে\s+)?(.+?)\s*(?:তে|এ|ে)?\s*নিয়ে\s+(?:যাও|চলো)"))
    _TRAILING_FILLER = re.compile(
        r"\s*(?:\b(?:please|pls|plz|now|right now|quickly|asap|on the (?:map|globe)|in 3d|"
        r"koro|kor|ekhon|ektu)\b|[.!?,;:])+\s*$",
        re.IGNORECASE,
    )

    def extract_destination(self, query: str) -> Optional[str]:
        """
        Extracts the navigation target from a fly-to style command.
        Returns None if the message is not a navigation command.
        """
        text = unicodedata.normalize("NFC", query.strip())
        m = self._EN_NAV.search(text)
        dest = m.group(1) if m else None
        if not dest:
            m = self._BANGLISH_NAV.search(text)
            if m:
                dest = m.group(1) or m.group(2)
        if not dest:
            m = self._BN_NAV.search(text)
            if m:
                dest = m.group(1)
        if not dest:
            return None
        # Strip trailing filler repeatedly ("new york now please!")
        prev = None
        while prev != dest:
            prev = dest
            dest = self._TRAILING_FILLER.sub("", dest).strip()
        # Strip trailing Banglish locative particle ("newyork e")
        dest = re.sub(r"\s+(?:e|te)$", "", dest, flags=re.IGNORECASE).strip()
        if not dest or len(dest) > 80:
            return None
        return dest

    @staticmethod
    def _match_preset(dest: str) -> Optional[Dict[str, Any]]:
        """Matches a destination string exactly (space/case-insensitive) to a known preset."""
        compact = re.sub(r"[\s'\-]", "", dest.lower())
        for key, loc in LOCATION_PRESETS.items():
            if compact == key or compact == re.sub(r"[\s'\-]", "", loc["name"].lower()):
                return loc
        bn_map = {"বাংলাদেশ": "bangladesh", "ঢাকা": "dhaka", "চট্টগ্রাম": "chittagong",
                  "সুন্দরবন": "sundarbans", "আমাজন": "amazon", "ক্যালিফোর্নিয়া": "california"}
        for bn, key in bn_map.items():
            if unicodedata.normalize("NFC", bn) in unicodedata.normalize("NFC", dest):
                return LOCATION_PRESETS[key]
        return None

    def extract_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """Extracts latitude and longitude from text if present."""
        matches = re.findall(r"[-+]?\d*\.\d+|\b[-+]?\d+\b", text)
        floats = []
        for m in matches:
            try:
                v = float(m)
                floats.append(v)
            except ValueError:
                pass
        if len(floats) >= 2:
            lat, lon = floats[0], floats[1]
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return (lat, lon)
        return None

    def detect_action(self, user_msg: str, highest_hotspot: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Detects if an interactive 3D UI action (fly-to, scenario trigger, sensor filter)
        should accompany the chatbot response.
        """
        lower = user_msg.lower()

        # 1. Ridge Crisis Scenario
        if any(w in lower for w in ["crisis", "scenario", "ridge", "সিনেরিও", "সিনারিও", "ক্রাইসিস"]):
            return {
                "type": "trigger_scenario",
                "label": "Execute Mountain Ridge Crisis Scenario",
                "params": {"scenario": "Dry Gale Wildfire Surge"}
            }

        # 2. Fly to Peak Fire Hotspot
        if any(w in lower for w in ["peak fire", "highest fire", "biggest fire", "max frp", "সবচেয়ে বড় আগুন", "সর্বোচ্চ আগুন"]):
            if highest_hotspot:
                return {
                    "type": "fly_to_coords",
                    "label": f"Fly to Peak Fire ({highest_hotspot.get('harmonized_frp', 0):.1f} MW)",
                    "params": {
                        "lat": highest_hotspot.get("latitude", 0.0),
                        "lon": highest_hotspot.get("longitude", 0.0),
                        "alt": 45000,
                        "hotspot_id": highest_hotspot.get("id", "")
                    }
                }

        # 3. Explicit navigation command ("fly to X") -> preset or live geocoding
        destination = self.extract_destination(user_msg)
        if destination and re.search(r"\b(fire|fires|hotspot|hotspots|frp|agun)\b", destination.lower()):
            # e.g. "fly to peak fire" with no live hotspot loaded - never geocode fire phrases
            return {"type": "unresolved_location", "label": destination, "params": {"query": destination, "reason": "no_hotspot"}}
        if destination:
            preset = self._match_preset(destination)
            if preset:
                return {
                    "type": "fly_to_preset",
                    "label": f"Fly to {preset['name']}",
                    "params": {"preset": preset["preset"], "lat": preset["lat"], "lon": preset["lon"], "alt": preset["alt"]},
                }
            coords = self.extract_coordinates(destination)
            if coords:
                return {
                    "type": "fly_to_coords",
                    "label": f"Fly to {coords[0]:.3f}, {coords[1]:.3f}",
                    "params": {"lat": coords[0], "lon": coords[1], "alt": 150000},
                }
            place = geocoding_service.geocode(destination)
            if place:
                return {
                    "type": "fly_to_coords",
                    "label": f"Fly to {place['short_name']}",
                    "params": {
                        "lat": place["lat"], "lon": place["lon"], "alt": place["alt"],
                        "place_name": place["name"], "provider": place["provider"],
                    },
                }
            # Navigation was requested but the place could not be resolved
            return {"type": "unresolved_location", "label": destination, "params": {"query": destination}}

        # 4. Known Geographical Presets mentioned in non-navigation messages (English & Bengali)
        lower_nfc = unicodedata.normalize("NFC", lower)
        for key, loc in LOCATION_PRESETS.items():
            if re.search(rf"\b{re.escape(key)}\b", lower_nfc):
                return {
                    "type": "fly_to_preset",
                    "label": f"Fly to {loc['name']}",
                    "params": {"preset": loc["preset"], "lat": loc["lat"], "lon": loc["lon"], "alt": loc["alt"]}
                }

        if "বাংলাদেশ" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to Bangladesh", "params": {"preset": "bangladesh", "lat": 23.85, "lon": 90.35, "alt": 750000}}
        if "ঢাকা" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to Dhaka", "params": {"preset": "dhaka", "lat": 23.81, "lon": 90.41, "alt": 85000}}
        if "চট্টগ্রাম" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to Chittagong", "params": {"preset": "chittagong", "lat": 22.35, "lon": 92.18, "alt": 110000}}
        if "সুন্দরবন" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to Sundarbans", "params": {"preset": "sundarbans", "lat": 22.15, "lon": 89.60, "alt": 95000}}
        if "আমাজন" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to Amazon", "params": {"preset": "amazon", "lat": -3.46, "lon": -62.21, "alt": 1800000}}
        if "ক্যালিফোর্নিয়া" in user_msg:
            return {"type": "fly_to_preset", "label": "Fly to California", "params": {"preset": "california", "lat": 36.77, "lon": -119.41, "alt": 950000}}

        # 4. Sensor Filter
        if "viirs only" in lower or "শুধু viirs" in lower:
            return {"type": "filter_sensor", "label": "Filter to VIIRS", "params": {"sensor": "VIIRS"}}
        if "modis only" in lower or "শুধু modis" in lower:
            return {"type": "filter_sensor", "label": "Filter to MODIS", "params": {"sensor": "MODIS"}}

        # 5. View Mode
        if "2d" in lower or "firms 2d" in lower:
            return {"type": "switch_view", "label": "Switch to FIRMS 2D", "params": {"mode": "firms"}}
        if "3d" in lower or "globe" in lower:
            return {"type": "switch_view", "label": "Switch to 3D Globe", "params": {"mode": "globe"}}

        return None


# Global intent router singleton
intent_router = IntentRouter()
