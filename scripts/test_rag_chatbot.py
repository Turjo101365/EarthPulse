"""
Comprehensive Automated Test Suite for EarthPulse RAG & AI Copilot
Verifies all 17 test questions specified in the NASA Space Apps requirements.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.chat.copilot_service import copilot_service
from backend.app.db.postgres import db_manager

TEST_QUESTIONS = [
    (1, "What is MODIS?", "rag", ["MODIS", "Terra", "Aqua"]),
    (2, "What is VIIRS?", "rag", ["VIIRS", "375", "Suomi-NPP"]),
    (3, "What is FRP?", "rag", ["FRP", "Megawatts", "Wooster"]),
    (4, "What is MCD14ML?", "rag", ["MCD14ML", "1km", "MODIS"]),
    (5, "What is VNP14IMGML?", "rag", ["VNP14IMGML", "375", "VIIRS"]),
    (6, "Why is VIIRS 375m useful?", "rag", ["375", "sub-pixel", "spatial"]),
    (7, "How do MODIS and VIIRS differ?", "rag", ["MODIS", "VIIRS", "resolution"]),
    (8, "What is MODIS–VIIRS harmonization?", "rag", ["harmoniz", "0.65", "H3"]),
    (9, "Which satellites provide VIIRS data?", "rag", ["Suomi-NPP", "NOAA-20", "NOAA-21"]),
    (10, "What is burned area?", "rag", ["Burned Area", "scar", "vegetation"]),
    (11, "What is MCD64A1?", "rag", ["MCD64A1", "500", "MODIS"]),
    (12, "What is VNP64A1?", "rag", ["VNP64A1", "500", "VIIRS"]),
    (13, "How does XGBoost fit into this project?", "rag", ["XGBoost", "Spatial Block", "PR-AUC"]),
    (14, "What is the current hotspot count?", "live_data", ["Hotspots", "detections"]),
    (15, "What is the predicted fire risk for coordinates 23.85, 90.35?", "ml_prediction", ["XGBoost", "probability"]),
    (16, "Why is it useful?", "follow_up", ["FRP", "Science", "biomass"]),
    (17, "What is the quantum teleportation frequency of Voyager 1 in 2029?", "unsupported", ["enough information"]),
]

def run_tests():
    print("======================================================================")
    print("🧪 Running EarthPulse RAG & AI Copilot Test Suite (17 Scenarios)")
    print("======================================================================")

    session_id = "test-session-suite-001"
    db_manager.clear_conversation_history(session_id)

    passed = 0
    failed = 0

    # First ask FRP so #16 follow-up makes sense
    print("\n--- Seeding context for follow-up testing ---")
    seed_res = copilot_service.query("What is Fire Radiative Power (FRP)?", conversation_id=session_id)
    print(f"Seed Question executed: {seed_res['answer'][:90]}...")

    for q_num, question, expected_intent, expected_keywords in TEST_QUESTIONS:
        print(f"\n[{q_num}/17] Testing: '{question}'")
        res = copilot_service.query(message=question, conversation_id=session_id)
        
        actual_intent = res["intent"]
        answer = res["answer"]
        sources = res.get("sources", [])
        retrieved = res["metadata"].get("retrievedChunks", 0)

        print(f"  • Detected Intent: {actual_intent} (Expected: {expected_intent})")
        print(f"  • Retrieved Chunks: {retrieved}")
        print(f"  • Citations: {[s['title'] for s in sources[:2]]}")
        print(f"  • Answer Preview: {answer[:130]}...")

        # Validation checks
        intent_ok = True
        if expected_intent == "follow_up":
            # Follow-up can be rag
            intent_ok = actual_intent in ("rag", "live_data")
        elif expected_intent != "unsupported":
            intent_ok = (actual_intent == expected_intent) or (expected_intent == "ml_prediction" and actual_intent in ("ml_prediction", "hybrid"))

        keywords_ok = any(kw.lower() in answer.lower() for kw in expected_keywords)
        
        if q_num == 17:
            # Must avoid hallucination
            no_hallucination = "not have enough information" in answer.lower() or "enough information" in answer.lower() or "পর্যাপ্ত তথ্য নেই" in answer
            keywords_ok = no_hallucination

        if intent_ok and keywords_ok:
            print("  ✅ PASSED")
            passed += 1
        else:
            print(f"  ⚠️ FAILED (intent_ok={intent_ok}, keywords_ok={keywords_ok})")
            failed += 1

    print("\n======================================================================")
    print(f"🏁 Test Results: {passed} PASSED, {failed} FAILED (Total: {len(TEST_QUESTIONS)})")
    print("======================================================================")

    # Test Bengali and Banglish queries
    print("\n🇧🇩 Testing Multilingual Capabilities:")
    bn_res = copilot_service.query("মোডিস এবং ভিয়ার্স এর পার্থক্য কী?", conversation_id=session_id)
    print("Bengali Response:")
    print(bn_res["answer"][:180] + "...\n")

    banglish_res = copilot_service.query("FRP ki ebong eta keno dorkar?", conversation_id=session_id)
    print("Banglish Response:")
    print(banglish_res["answer"][:180] + "...\n")

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
