"""
PulseAI Wildfire Copilot & Tactical Telemetry Assistant
Features RAG Knowledge Retrieval, Live Telemetry Grounding,
Action Dispatching (Cesium 3D camera fly-to, scenario trigger, sensor filters),
Multilingual NLP (English, Bengali, Banglish), and LangSmith Observability.
"""

import os
import re
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..rag import rag_retriever
from ...spatial_index import spatial_index, GLOBAL_COUNTRY_ANCHORS
from ...data_generator import get_all_hotspots
from ..telemetry import langsmith_tracer, metrics_manager

# Known geographic presets mapping to camera targets
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
    "japan": {"name": "Japan", "lat": 36.20, "lon": 138.25, "alt": 1600000, "preset": "japan"},
    "australia": {"name": "Australia", "lat": -25.27, "lon": 133.77, "alt": 3500000, "preset": "australia"},
    "greece": {"name": "Greece Arc", "lat": 39.07, "lon": 21.82, "alt": 750000, "preset": "greece"},
    "spain": {"name": "Spain", "lat": 40.46, "lon": -3.74, "alt": 900000, "preset": "spain"},
    "congo": {"name": "Congo Basin", "lat": -4.03, "lon": 21.75, "alt": 1800000, "preset": "congo"},
    "canada": {"name": "Canada", "lat": 56.13, "lon": -106.34, "alt": 4200000, "preset": "canada"},
}

def is_bengali_query(text: str) -> bool:
    """Detects whether text contains Bengali Unicode characters or common Banglish words."""
    # Bengali unicode range: \u0980-\u09FF
    if re.search(r'[\u0980-\u09FF]', text):
        return True
    banglish_markers = [
        "koro", "koroo", "bolo", "ki", "kemon", "ache", "aagun", "agun",
        "shobcheye", "sobcheye", "dekhao", "jao", "bistarito", "bujhiye", "kothay"
    ]
    tokens = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    return len(tokens.intersection(banglish_markers)) >= 1

class CopilotService:
    def __init__(self):
        self.retriever = rag_retriever

    def get_live_telemetry_snapshot(self) -> Dict[str, Any]:
        """Gathers real-time telemetry metrics from spatial index and models."""
        hotspots = spatial_index.hotspots
        summary = spatial_index.global_summary
        
        # Identify highest FRP hotspot
        top_hotspots = sorted(hotspots, key=lambda x: x.get("harmonized_frp", 0.0), reverse=True)[:5]
        max_hotspot = top_hotspots[0] if top_hotspots else None

        return {
            "total_hotspots": len(hotspots),
            "modis_count": summary.get("modis_count", 0),
            "viirs_count": summary.get("viirs_count", 0),
            "avg_frp": summary.get("avg_frp", 0.0),
            "max_frp": summary.get("max_frp", 0.0),
            "high_risk_count": summary.get("high_risk_count", 0),
            "burned_area_sqkm": summary.get("burned_area_sqkm", 0.0),
            "carbon_co2_mt": summary.get("carbon_co2_mt", 0.0),
            "total_energy_gw": summary.get("total_energy_gw", 0.0),
            "highest_hotspot": max_hotspot,
            "top_hotspots": top_hotspots
        }

    def detect_action(self, user_msg: str, telemetry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyzes the user request to determine if an interactive UI action should be triggered:
        fly_to, trigger_scenario, filter_sensor, switch_view, sync_firms, etc.
        """
        lower = user_msg.lower()

        # 1. Ridge Crisis Scenario
        if any(w in lower for w in ["crisis", "scenario", "ridge", "সিনেরিও", "সিনারিও", "ক্রাইসিস"]):
            return {
                "type": "trigger_scenario",
                "label": "Execute Mountain Ridge Crisis Scenario",
                "params": {"scenario": "Dry Gale Wildfire Surge"}
            }

        # 2. Highest FRP Hotspot Fly-To
        if any(w in lower for w in ["peak", "highest", "biggest", "max frp", "সবচেয়ে বড়", "সর্বোচ্চ", "বিপজ্জনক"]):
            if telemetry.get("highest_hotspot"):
                hh = telemetry["highest_hotspot"]
                return {
                    "type": "fly_to_coords",
                    "label": f"Fly to Peak Fire ({hh.get('harmonized_frp', 0):.1f} MW)",
                    "params": {
                        "lat": hh.get("latitude", 0.0),
                        "lon": hh.get("longitude", 0.0),
                        "alt": 45000,
                        "hotspot_id": hh.get("id", "")
                    }
                }

        # 3. Known Geographical Presets
        for key, loc in LOCATION_PRESETS.items():
            # Check english key or bengali names
            if key in lower:
                return {
                    "type": "fly_to_preset",
                    "label": f"Fly to {loc['name']}",
                    "params": {"preset": loc["preset"], "lat": loc["lat"], "lon": loc["lon"], "alt": loc["alt"]}
                }

        # Bengali transliterated locations
        if "বাংলাদেশ" in user_msg or "bangladesh" in lower:
            return {"type": "fly_to_preset", "label": "Fly to Bangladesh", "params": {"preset": "bangladesh", "lat": 23.85, "lon": 90.35, "alt": 750000}}
        if "ঢাকা" in user_msg or "dhaka" in lower:
            return {"type": "fly_to_preset", "label": "Fly to Dhaka", "params": {"preset": "dhaka", "lat": 23.81, "lon": 90.41, "alt": 85000}}
        if "চট্টগ্রাম" in user_msg or "chittagong" in lower:
            return {"type": "fly_to_preset", "label": "Fly to Chittagong", "params": {"preset": "chittagong", "lat": 22.35, "lon": 92.18, "alt": 110000}}
        if "সুন্দরবন" in user_msg or "sundarbans" in lower:
            return {"type": "fly_to_preset", "label": "Fly to Sundarbans", "params": {"preset": "sundarbans", "lat": 22.15, "lon": 89.60, "alt": 95000}}
        if "আমাজন" in user_msg or "amazon" in lower:
            return {"type": "fly_to_preset", "label": "Fly to Amazon", "params": {"preset": "amazon", "lat": -3.46, "lon": -62.21, "alt": 1800000}}
        if "ক্যালিফোর্নিয়া" in user_msg or "california" in lower:
            return {"type": "fly_to_preset", "label": "Fly to California", "params": {"preset": "california", "lat": 36.77, "lon": -119.41, "alt": 950000}}

        # 4. Sensor Filter
        if "viirs only" in lower or "শুধু viirs" in lower or "ভিয়ার্স" in lower:
            return {"type": "filter_sensor", "label": "Filter to VIIRS", "params": {"sensor": "VIIRS"}}
        if "modis only" in lower or "শুধু modis" in lower or "মোডিস" in lower:
            return {"type": "filter_sensor", "label": "Filter to MODIS", "params": {"sensor": "MODIS"}}

        # 5. View Mode
        if "2d" in lower or "firms 2d" in lower or "২ডি" in lower:
            return {"type": "switch_view", "label": "Switch to FIRMS 2D", "params": {"mode": "firms"}}
        if "3d" in lower or "globe" in lower or "৩ডি" in lower:
            return {"type": "switch_view", "label": "Switch to 3D Globe", "params": {"mode": "globe"}}

        # 6. Sync Live Data
        if any(w in lower for w in ["sync", "refresh", "ingest", "রিফ্রেশ", "সিঙ্ক"]):
            return {"type": "sync_firms", "label": "Sync Live NASA FIRMS Feed", "params": {}}

        return None

    def query(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        viewport: Optional[Dict[str, Any]] = None,
        provider: str = "builtin",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a conversational query:
        1. Retrieves RAG knowledge chunks
        2. Aggregates live spatial telemetry
        3. Detects actionable UI triggers
        4. Synthesizes grounded response (Built-in or Gemini / OpenAI)
        5. Logs LangSmith trace
        """
        t0 = time.time()
        bengali_mode = is_bengali_query(message)

        # 1. RAG Retrieval
        rag_chunks = self.retriever.retrieve(message, top_k=3)
        rag_context_str = self.retriever.format_rag_context(rag_chunks)

        # 2. Live Telemetry
        telemetry = self.get_live_telemetry_snapshot()

        # 3. Detect Action
        action = self.detect_action(message, telemetry)

        # 4. Generate Response
        reply = ""
        model_name = "Built-in Mission Control AI"
        tokens_prompt = 420
        tokens_completion = 180

        # Check for Gemini / OpenAI invocation if requested
        gemini_key = api_key or os.getenv("GEMINI_API_KEY", "")
        openai_key = api_key or os.getenv("OPENAI_API_KEY", "")

        if provider == "gemini" and gemini_key:
            try:
                reply, model_name = self._call_gemini(message, history, rag_context_str, telemetry, gemini_key, model)
            except Exception as e:
                print(f"Gemini API fallback to builtin ({e})")
                reply = self._generate_builtin_reply(message, rag_chunks, telemetry, action, bengali_mode)
                model_name = f"Built-in Fallback (Gemini: {str(e)[:30]})"
        elif provider == "openai" and openai_key:
            try:
                reply, model_name = self._call_openai(message, history, rag_context_str, telemetry, openai_key, model)
            except Exception as e:
                print(f"OpenAI API fallback to builtin ({e})")
                reply = self._generate_builtin_reply(message, rag_chunks, telemetry, action, bengali_mode)
                model_name = f"Built-in Fallback (OpenAI: {str(e)[:30]})"
        else:
            reply = self._generate_builtin_reply(message, rag_chunks, telemetry, action, bengali_mode)

        latency_ms = round((time.time() - t0) * 1000, 1)

        # 5. Anti-Hallucination & Grounding Evaluation
        eval_result = self.retriever.evaluate_grounding(reply, rag_chunks)

        # 6. Record in LangSmith
        hh_dict = telemetry.get("highest_hotspot") or {}
        trace = langsmith_tracer.trace_dispatch_explanation(
            hotspot_id=hh_dict.get("id", "H3-GLOBAL"),
            rl_action=action.get("type", "CHAT_QUERY_GROUNDED") if action else "CHAT_QUERY_GROUNDED",
            slope_deg=24.0,
            wind_desc="Telemetry-grounded copilot query",
            playbook=f"RAG Citations: {', '.join(eval_result['citations']) or 'Core Spatial Index'}",
            tactical_order=reply[:240] + ("..." if len(reply) > 240 else "")
        )

        return {
            "reply": reply,
            "action": action,
            "rag": {
                "chunks_retrieved": len(rag_chunks),
                "citations": eval_result["citations"],
                "grounding_score": eval_result["grounding_score"],
                "facts_grounded_pct": eval_result["facts_grounded_pct"],
                "status": eval_result["status"]
            },
            "grounding": {
                "catalog_size": telemetry["total_hotspots"],
                "avg_frp": telemetry["avg_frp"],
                "max_frp": telemetry["max_frp"],
                "model_used": model_name,
                "latency_ms": latency_ms
            },
            "trace_id": trace.get("trace_id", "ls-trace-0001")
        }

    def _generate_builtin_reply(
        self,
        query: str,
        rag_chunks: List[Dict[str, Any]],
        telemetry: Dict[str, Any],
        action: Optional[Dict[str, Any]],
        bengali: bool
    ) -> str:
        """
        Deep, domain-grounded Built-in Mission Control AI Engine.
        Synthesizes RAG technical knowledge and real-time telemetry.
        """
        lower = query.lower()
        tot = telemetry["total_hotspots"]
        avg_frp = telemetry["avg_frp"]
        max_frp = telemetry["max_frp"]
        burned = telemetry["burned_area_sqkm"]
        co2 = telemetry["carbon_co2_mt"]
        hh = telemetry.get("highest_hotspot")

        # Check if user explicitly asked for navigation vs asking an informational question
        is_explicit_nav_cmd = any(w in lower for w in ["fly", "go to", "take me", "navigate", "jump", "নিয়ে যাও", "যাও", "দেখাও"]) and not any(w in lower for w in ["অবস্থা", "status", "kemon", "কি", "কেন", "why", "what", "how", "পার্থক্য"])

        # 1. Action Confirmation Prompts (for pure explicit commands)
        if action and is_explicit_nav_cmd:
            if action["type"] == "trigger_scenario":
                if bengali:
                    return (
                        f"⚡ **Ridge Crisis Scenario ট্রিগার করা হচ্ছে!**\n\n"
                        f"**দৃশ্যপট:** Mountain Ridge Wildfire Surge (শুষ্ক দমকা বাতাস ও উচ্চ FRP)।\n"
                        f"- **Harmonizer:** ৩টি VIIRS ও ১টি MODIS পিং ফিউজ করে FRP: 112 MW গণনা করেছে।\n"
                        f"- **XGBoost:** আবাসিক Valley Sector B-এর দিকে ৪ ঘণ্টায় ৮৯% ছড়ানোর সম্ভাবনা পূর্বাভাস দিয়েছে।\n"
                        f"- **RL Agent (PPO):** ৫০০টি রোলআউট শেষে পর্বতের রিজ বরাবর ২টি Air Tanker রিটার্ড্যান্ট ড্রপের সিদ্ধান্ত নিয়েছে।\n\n"
                        f"গ্লোবে ৩D কনট্যুর এবং কন্টেনমেন্ট লাইন রেন্ডার হচ্ছে।"
                    )
                else:
                    return (
                        f"⚡ **Triggering Mountain Ridge Crisis Scenario!**\n\n"
                        f"**Scenario Profile:** Dry Gale Wildfire Surge along Mountain Ridge.\n"
                        f"- **Harmonizer:** Fused 3 VIIRS + 1 MODIS detection into 1 unified hotspot (Calibrated FRP: 112 MW).\n"
                        f"- **XGBoost:** Forecasts 89% spread probability towards residential Valley Sector B in 4 hours.\n"
                        f"- **RL Agent (PPO):** Solved optimal intervention: 2 Air Tankers deployed to cut fireline along Mountain Ridge H3-8826.\n\n"
                        f"3D contours and containment lines are now rendering on Cesium globe."
                    )

            if action["type"] in ("fly_to_preset", "fly_to_coords"):
                loc_name = action.get("label", "Target Area")
                if bengali:
                    return (
                        f"🚀 **ক্যামেরা মুভ হচ্ছে:** {loc_name}!\n\n"
                        f"গ্লোব ক্যামেরা স্বয়ংক্রিয়ভাবে উক্ত অঞ্চলের ভৌগোলিক কোঅর্ডিনেটসে ফ্লাই করছে। "
                        f"বর্তমান উচ্চতা অনুযায়ী ডায়নামিক LOD (Level of Detail) সক্রিয় রয়েছে।"
                    )
                else:
                    return (
                        f"🚀 **Flying camera to:** {loc_name}!\n\n"
                        f"The Cesium 3D camera is flying smoothly to the target geographic coordinates. "
                        f"Altitude-driven Level-of-Detail (LOD) indexing is dynamically adjusting to display local hotspots."
                    )

            if action["type"] == "filter_sensor":
                sens = action["params"]["sensor"]
                if bengali:
                    return f"🛰️ **সেন্সর ফিল্টার আপডেট:** এখন শুধুমাত্র **{sens}** স্যাটেলাইট ডিটেকশন দেখানো হচ্ছে।"
                else:
                    return f"🛰️ **Sensor Filter Applied:** Displaying active detections exclusively from **{sens}**."

        # 2. General Fire Summary / Status
        if any(w in lower for w in ["summary", "status", "overview", "অবস্থা", "কেমন", "পরিস্থিতি", "কত", "সব"]):
            if bengali:
                return (
                    f"🌍 **গ্লোবাল ওয়াইল্ডফায়ার মিশন কন্ট্রোল সারাংশ:**\n\n"
                    f"- **সক্রিয় স্যাটেলাইট হটস্পট:** `{tot:,}` টি ডিটেকশন (MODIS: `{telemetry['modis_count']:,}` | VIIRS: `{telemetry['viirs_count']:,}`)\n"
                    f"- **গড় অগ্নিকিরণ শক্তি (FRP):** `{avg_frp} MW`\n"
                    f"- **সর্বোচ্চ FRP পিক:** `{max_frp} MW` (সবচেয়ে বিপজ্জনক আগুন)\n"
                    f"- **আনুমানিক পোড়া অঞ্চল:** `{burned:,.1f} km²`\n"
                    f"- **বায়ুমণ্ডলে কার্বন নিঃসরণ:** `{co2:.2f} Mt CO₂`\n"
                    f"- **মোট থার্মাল এনার্জি:** `{telemetry['total_energy_gw']:.1f} GW`\n\n"
                    f"💡 আপনি নির্দিষ্ট কোনো এলাকা (যেমন: *'Fly to California'* বা *'আমাজনে যাও'*) দেখতে চাইতে পারেন অথবা *'সবচেয়ে বড় আগুন দেখাও'* বলতে পারেন।"
                )
            else:
                return (
                    f"🌍 **Planetary Wildfire Mission Control Summary:**\n\n"
                    f"- **Active Satellite Hotspots:** `{tot:,}` detections (MODIS: `{telemetry['modis_count']:,}` | VIIRS: `{telemetry['viirs_count']:,}`)\n"
                    f"- **Mean Fire Radiative Power (FRP):** `{avg_frp} MW`\n"
                    f"- **Peak FRP Surge:** `{max_frp} MW` (Highest intensity fire)\n"
                    f"- **Estimated Burned Area:** `{burned:,.1f} km²`\n"
                    f"- **Atmospheric Carbon Released:** `{co2:.2f} Mt CO₂`\n"
                    f"- **Radiative Thermal Output:** `{telemetry['total_energy_gw']:.1f} GW`\n\n"
                    f"💡 Ask me to *'Fly to California'*, *'Show Amazon Basin'*, or *'Run Ridge Crisis Scenario'* for real-time 3D tactical actions."
                )

        # 3. Highest Fire / Peak Hotspot
        if any(w in lower for w in ["highest", "peak", "worst", "বিপজ্জনক", "সবচেয়ে বড়", "সর্বোচ্চ"]):
            if hh:
                lat = hh.get("latitude", 0.0)
                lon = hh.get("longitude", 0.0)
                frp = hh.get("harmonized_frp", 0.0)
                sens = hh.get("sensor", "VIIRS")
                if bengali:
                    return (
                        f"🔥 **বর্তমান বিশ্বের সর্বোচ্চ তীব্রতার আগুন:**\n\n"
                        f"- **তীব্রতা (FRP):** `{frp:.1f} MW`\n"
                        f"- **স্থানাঙ্ক:** `{lat:.3f}° N, {lon:.3f}° E`\n"
                        f"- **ডিটেক্টিং সেন্সর:** `{sens}`\n"
                        f"- **ঝুঁকির মাত্রা:** `{hh.get('risk_level', 'CRITICAL')}`\n\n"
                        f"👉 ক্যামেরা সরাসরি এই আগুনে নিয়ে যেতে লিখুন: **'Fly to peak fire'**।"
                    )
                else:
                    return (
                        f"🔥 **Global Peak FRP Wildfire Detection:**\n\n"
                        f"- **Radiative Power:** `{frp:.1f} MW` (CRITICAL)\n"
                        f"- **Coordinates:** `{lat:.3f}° N, {lon:.3f}° E`\n"
                        f"- **Detecting Sensor:** `{sens}`\n"
                        f"- **Risk Classification:** `{hh.get('risk_level', 'CRITICAL')}`\n\n"
                        f"👉 Say **'Fly to peak fire'** to center the Cesium camera on this hotspot."
                    )

        # 4. Regional / Bangladesh Query
        if any(w in lower for w in ["bangladesh", "dhaka", "chittagong", "sundarbans", "বাংলাদেশ", "চট্টগ্রাম", "সুন্দরবন"]):
            # Find hotspots near Bangladesh (approx lat 20.5-26.5, lon 88.0-92.8)
            bd_hotspots = [h for h in spatial_index.hotspots if 20.5 <= h.get("latitude", 0) <= 26.5 and 88.0 <= h.get("longitude", 0) <= 92.8]
            count = len(bd_hotspots)
            if bengali:
                return (
                    f"🇧🇩 **বাংলাদেশ ও সংলগ্ন অঞ্চলের অগ্নিকাণ্ড টেলিমেট্রি:**\n\n"
                    f"- **শনাক্তকৃত হটস্পট সংখ্যা:** `{count}` টি\n"
                    f"- **মূল উৎস:** কৃষি ফসল কাটার পর নাড়া পোড়ানো (Crop residue burning) এবং চট্টগ্রাম পার্বত্য অঞ্চলের (CHT) ঝুম চাষ এলাকা।\n"
                    f"- **সুন্দরবন ম্যানগ্রোভ:** সংবেদনশীল সংরক্ষিত বনাঞ্চলের প্রান্তে কোনো বড় থার্মাল অ্যানোমালি থাকলে রিয়েল-টাইমে অ্যালার্ট জারি হয়।\n"
                    f"- **সাধারণ FRP সীমা:** ১৫–৬০ MW (নিম্ন থেকে মাঝারি তীব্রতা)।\n\n"
                    f"👉 গ্লোবে দেখতে বলুন: **'Fly to Bangladesh'** বা **'সুন্দরবনে যাও'**।"
                )
            else:
                return (
                    f"🇧🇩 **Bangladesh & Regional Fire Telemetry:**\n\n"
                    f"- **Active Detections in Sector:** `{count}` hotspots\n"
                    f"- **Primary Sources:** Seasonal agricultural residue clearing and localized shifting cultivation in Chittagong Hill Tracts (CHT).\n"
                    f"- **Sundarbans Biosphere:** Continuous buffer monitoring for sensitive mangrove fringe protection.\n"
                    f"- **Typical FRP Profile:** 15–60 MW (Low to Moderate severity).\n\n"
                    f"👉 Say **'Fly to Bangladesh'** or **'Fly to Chittagong'** to inspect 3D terrain."
                )

        # 5. Technical Questions on Remote Sensing (MODIS vs VIIRS, H3, FRP)
        if any(w in lower for w in ["modis", "viirs", "sensor", "resolution", "পার্থক্য"]):
            top_chunk = rag_chunks[0] if rag_chunks else {}
            if bengali:
                return (
                    f"🛰️ **NASA FIRMS: MODIS বনাম VIIRS তুলনা:**\n\n"
                    f"1. **MODIS (Terra & Aqua):**\n"
                    f"   - স্থানিক রেজোলিউশন: **১,০০০ মিটার (১ কিমি)**।\n"
                    f"   - ২০০০ সাল থেকে ২৪ বছরের ধারাবাহিক ক্লাইমেট হিস্টোরিক্যাল বেসলাইন রয়েছে।\n"
                    f"2. **VIIRS (Suomi-NPP & NOAA-20):**\n"
                    f"   - স্থানিক রেজোলিউশন: **৩৭৫ মিটার** (৩ গুণ বেশি নিখুঁত)।\n"
                    f"   - ছোট সাব-পিক্সেল আগুন শনাক্ত করতে অনেক বেশি সংবেদনশীল এবং সোয়াথ প্রান্তে ছবির বিকৃতি কম।\n\n"
                    f"3. **EarthPulse Harmonization:**\n"
                    f"   দুটো সেন্সরকে সমান আয়তনের **H3 Hexagonal Grid (Res 8/9)**-এ ম্যাপ করা হয় এবং DBSCAN ক্লাস্টারিং দিয়ে ডুপ্লিকেট পিং মার্জ করে ক্যালিফ্রেটেড FRP বের করা হয়:\n"
                    f"   `FRP = 0.65 × VIIRS + 0.35 × MODIS`।"
                )
            else:
                return (
                    f"🛰️ **NASA FIRMS Sensor Harmonization (MODIS vs VIIRS):**\n\n"
                    f"1. **MODIS (Terra & Aqua):**\n"
                    f"   - Spatial Resolution: **1,000 meters (1 km)** at nadir.\n"
                    f"   - 24-year historical baseline (2000–present), broader optical Point Spread Function.\n"
                    f"2. **VIIRS (Suomi-NPP & NOAA-20):**\n"
                    f"   - Spatial Resolution: **375 meters** (3x sharper).\n"
                    f"   - High sensitivity to small sub-pixel fires with lower optical distortion at scan edges.\n\n"
                    f"3. **Harmonization Core:**\n"
                    f"   Both feeds are indexed onto equal-area **Uber H3 hexagonal cells (Res 8/9)**, deduplicated with DBSCAN (1000m), and calibrated via:\n"
                    f"   `FRP_harmonized = 0.65 * FRP_viirs + 0.35 * FRP_modis`."
                )

        # 6. Machine Learning (XGBoost, Spatial Split)
        if any(w in lower for w in ["xgboost", "ml", "spatial split", "leakage", "machine learning", "মডেল"]):
            if bengali:
                return (
                    f"🧠 **Predictive ML: Spatial Block Holdout & XGBoost:**\n\n"
                    f"- **সমস্যা (Data Leakage):** ওয়াইল্ডফায়ার মডেলে সাধারণ র‍্যান্ডম K-Fold ব্যবহার করলে পাশাপাশি পিক্সেলগুলোর মধ্যে স্থানিক অটোকোরিলেশনের কারণে কৃত্রিমভাবে অতিরিক্ত অ্যাকুরেসি দেখায়।\n"
                    f"- **EarthPulse সমাধান:** পুরো মহাদেশকে **৫০ কিমি × ৫০ কিমি ব্লক**-এ ভাগ করে সম্পূর্ণ ব্লক টেস্ট সেটে আলাদা রাখা হয় (Spatial Block Holdout)।\n"
                    f"- **মডেল:** XGBoost (ARM64 hist engine) এবং PyTorch Apple Metal Performance Shaders (MPS)।\n"
                    f"- **মূল মেট্রিক:** `PR-AUC = 0.84` (অসম ডাটার ক্ষেত্রে ROC-AUC এর চেয়ে নির্ভরযোগ্য)।\n"
                    f"- **ফিচারসমূহ:** Lag-FRP (t-24h), Fire Weather Index (FWI), আপেক্ষিক আর্দ্রতা, বাতাসের বেগ এবং DEM পাহাড়ের ঢাল।"
                )
            else:
                return (
                    f"🧠 **Predictive ML: Zero-Leakage Spatial Block Holdout & XGBoost:**\n\n"
                    f"- **Anti-Leakage Strategy:** Traditional random K-Fold leaks spatial autocorrelation between neighboring fire pixels. EarthPulse enforces **Spatial Block Holdout (50 km × 50 km blocks)** to test true out-of-region generalization skill.\n"
                    f"- **Engines:** XGBoost ARM64 hist engine + Apple Metal MPS PyTorch GPU.\n"
                    f"- **Evaluation Metric:** `PR-AUC = 0.84` with `scale_pos_weight = 14.2` to counter severe wildfire sparsity.\n"
                    f"- **Predictive Features:** Lag-FRP (t-24h), Fire Weather Index (FWI), Relative Humidity, Wind vector alignment, and DEM slope."
                )

        # 7. Reinforcement Learning (PPO, Suppression)
        if any(w in lower for w in ["rl", "ppo", "reinforcement", "suppression", "tanker", "বুলডোজার"]):
            if bengali:
                return (
                    f"🛡️ **Prescriptive RL: PPO Agent & ফায়ার সাপ্রেশন:**\n\n"
                    f"- কেবল আগুনের পূর্বাভাস নয়, EarthPulse এর **PPO (Proximal Policy Optimization)** এজেন্ট স্বয়ংক্রিয়ভাবে সর্বোত্তম অগ্নিনির্বাপক সম্পদ মোতায়েনের সিদ্ধান্ত নেয়।\n"
                    f"- **অ্যাকশন স্পেস:**\n"
                    f"  1. `DC-10 Air Tanker` (রিটার্ড্যান্ট কেমিক্যাল ড্রপ করে আগুনের অগ্রযাত্রা থামায়)\n"
                    f"  2. `Bulldozer Fireline` (মাটির খনিজ স্তর বের করে ফায়ারব্রেক কাটে)\n"
                    f"  3. `Evacuation Corridor` (নাগরিকদের নিরাপদে সরে যাওয়ার করিডোর নিশ্চিত করে)\n"
                    f"- **রিওয়ার্ড ফাংশন:** বন পোড়া এবং বাড়িঘরের ঝুঁকিকে নেতিবাচক এবং কন্টেনমেন্ট নিশ্চিত করাকে উচ্চ ধনাত্মক রিওয়ার্ড দেয়।"
                )
            else:
                return (
                    f"🛡️ **Prescriptive RL: PPO Agent & Autonomous Suppression:**\n\n"
                    f"- Rather than passive heatmaps, FireGuard AI uses **PPO Reinforcement Learning** in Gymnasium to optimize emergency response.\n"
                    f"- **Action Space:**\n"
                    f"  1. `DC-10 Air Tanker`: Long-term chemical retardant drops ahead of convective fire fronts.\n"
                    f"  2. `Bulldozer Firelines`: Rapid mineral soil breaks.\n"
                    f"  3. `Evacuation Corridors`: Civilian safe-egress enforcement.\n"
                    f"- **Policy Optimization:** Learned to establish ridge containment lines 1.5–2 hours ahead of the fireline, maximizing saved hectares."
                )

        # 8. RAG Subsystem Explanation
        if any(w in lower for w in ["rag", "retrieval", "knowledge base", "ভেক্টর", "আরএজি"]):
            if bengali:
                return (
                    f"📚 **EarthPulse RAG (Retrieval-Augmented Generation) সিস্টেম:**\n\n"
                    f"- **ভেক্টর ইনডেক্সিং:** Scikit-Learn `TfidfVectorizer` (sublinear TF, n-grams 1-2) এবং কোসাইন সিমিলারিটি দিয়ে টেকনিক্যাল নলেজ চ্যাঙ্কস ইনডেক্স করা হয়েছে।\n"
                    f"- **ডোমেইন নলেজ:** NASA FIRMS সেন্সর স্পেসিফিকেশন, FRP থার্মোডাইনামিক্স, H3 হেক্সাগন গ্রিড, XGBoost স্পেশাল স্প্লিট, PPO সাপ্রেশন রিওয়ার্ড এবং ICS ট্যাকটিক্যাল প্লেবুক।\n"
                    f"- **অ্যান্টি-হ্যালুসিনেশন চেক:** প্রতিটি উত্তরের সত্যতা নলেজ বেসের সাথে মিলিয়ে যাচাই করা হয় (Grounding Score) এবং LangSmith অডিট ট্রেল-এ রেকর্ড করা হয়।"
                )
            else:
                return (
                    f"📚 **EarthPulse RAG (Retrieval-Augmented Generation) Architecture:**\n\n"
                    f"- **Vector Indexing:** Sublinear TF-IDF vectorization with n-gram range (1, 2) and cosine similarity ranking.\n"
                    f"- **Domain Knowledge Base:** Curated specs on NASA FIRMS (MODIS/VIIRS), FRP biomass math, H3 hexagonal indexing, Spatial Block Holdout ML, PPO suppression policies, and ICS ridge containment.\n"
                    f"- **Anti-Hallucination Guardrail:** Every response is verified for factual grounding before logging to LangSmith audit traces."
                )

        # Default fallback using top RAG chunk
        top_c = rag_chunks[0] if rag_chunks else None
        if top_c:
            c_title = top_c["title"]
            c_text = top_c["content"]
            if bengali:
                return (
                    f"🛰️ **টেলিমেট্রি ইন্টেলিজেন্স রিপোর্ট ({c_title}):**\n\n"
                    f"{c_text}\n\n"
                    f"📊 **বর্তমান সক্রিয় পরিস্থিতি:** `{tot:,}` টি স্যাটেলাইট হটস্পট, পিক FRP `{max_frp} MW`।\n"
                    f"কোনো এলাকা দেখতে চাইলে বলুন *'Fly to California'* বা *'সিনারিও রান করো'*।"
                )
            else:
                return (
                    f"🛰️ **Telemetry Intelligence Report ({c_title}):**\n\n"
                    f"{c_text}\n\n"
                    f"📊 **Current Live Telemetry:** `{tot:,}` active satellite hotspots, Peak FRP: `{max_frp} MW`.\n"
                    f"Ask me to navigate anywhere (e.g. *'Fly to Amazon'* or *'Run Ridge Crisis Scenario'*)."
                )

        # Fallback general
        if bengali:
            return (
                f"🌍 **EarthPulse Copilot প্রস্তুত!**\n\n"
                f"আমি নাসা স্যাটেলাইট টেলিমেট্রি, FRP অগ্নিকিরণ শক্তি, XGBoost পূর্বাভাস এবং PPO ফায়ারফাইটিং ডিসপ্যাচে সহায়তা করতে পারি।\n"
                f"আপনি যেকোনো প্রশ্ন করতে পারেন অথবা গ্লোবে নেভিগেট করতে বলতে পারেন (যেমন: *'আমাজনে নিয়ে যাও'*, *'সর্বোচ্চ আগুন দেখাও'* বা *'সিনারিও রান করো'*)।"
            )
        else:
            return (
                f"🌍 **EarthPulse AI Copilot Ready!**\n\n"
                f"I am fully grounded in NASA FIRMS satellite observations, FRP power metrics, XGBoost spatial spread forecasts, and PPO suppression tactics.\n"
                f"Try asking: *'What is the current global fire summary?'*, *'Fly to peak fire'*, or *'Run Ridge Crisis Scenario'*."
            )

    def _call_gemini(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]],
        rag_context: str,
        telemetry: Dict[str, Any],
        api_key: str,
        model: Optional[str]
    ) -> tuple[str, str]:
        """Calls Google Gemini REST API with telemetry and RAG grounding."""
        model_name = model or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        system_instruction = (
            "You are PulseAI, the tactical AI Mission Copilot for EarthPulse 3D & FireGuard AI (NASA Space Apps). "
            "You provide authoritative, telemetry-grounded wildfire analytics, spatial remote sensing guidance, "
            "and tactical firefighting recommendations. "
            "Respond in the same language as the user (English or Bengali). "
            f"Live Telemetry: Total Hotspots={telemetry['total_hotspots']}, Avg FRP={telemetry['avg_frp']} MW, "
            f"Peak FRP={telemetry['max_frp']} MW, Burned Area={telemetry['burned_area_sqkm']} km2, Carbon={telemetry['carbon_co2_mt']} Mt CO2.\n"
            f"{rag_context}"
        )

        contents = []
        if history:
            for h in history[-4:]:
                contents.append({
                    "role": "user" if h.get("role") == "user" else "model",
                    "parts": [{"text": h.get("content", "")}]
                })
        contents.append({
            "role": "user",
            "parts": [{"text": f"[User Query]: {query}"}]
        })

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 600,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                return text, f"Google {model_name}"
            raise ValueError("No candidates returned from Gemini API")

    def _call_openai(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]],
        rag_context: str,
        telemetry: Dict[str, Any],
        api_key: str,
        model: Optional[str]
    ) -> tuple[str, str]:
        """Calls OpenAI REST API with telemetry and RAG grounding."""
        model_name = model or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are PulseAI, tactical AI Mission Copilot for EarthPulse 3D & FireGuard AI (NASA Space Apps). "
                    "Respond authoritatively, grounded in real telemetry. Support English and Bengali. "
                    f"Live Telemetry: Hotspots={telemetry['total_hotspots']}, Avg FRP={telemetry['avg_frp']} MW, "
                    f"Peak FRP={telemetry['max_frp']} MW.\n{rag_context}"
                )
            }
        ]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": query})

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 600
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            reply = data["choices"][0]["message"]["content"]
            return reply, f"OpenAI {model_name}"

# Global singleton copilot service
copilot_service = CopilotService()
