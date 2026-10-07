"""
Verification script for EarthPulse Real-Time Web Search Integration
Tests both English and Banglish/Bangla web search queries,
validating intent classification, live external news retrieval,
clickable URL extraction, and response synthesis.
"""

import urllib.request
import json
import sys

BASE_URL = "http://localhost:8050/api/chat"

TESTS = [
    {
        "name": "English Web Search Query",
        "message": "Search web for latest NASA wildfire news",
        "expect_intent": "web_search"
    },
    {
        "name": "Banglish Web Search Query",
        "message": "Web search koro: Greece e aguner latest news ki?",
        "expect_intent": "web_search"
    },
    {
        "name": "Breaking News Query",
        "message": "What is the latest breaking news on California wildfires?",
        "expect_intent": "web_search"
    }
]

def run_tests():
    passed = 0
    failed = 0
    print("\n" + "=" * 70)
    print("      EARTHPULSE REAL-TIME WEB SEARCH INTEGRATION TESTS")
    print("=" * 70)

    for i, test in enumerate(TESTS, 1):
        print(f"\n[{i}/{len(TESTS)}] Running: {test['name']}")
        print(f"Message: \"{test['message']}\"")
        payload = json.dumps({"message": test["message"]}).encode("utf-8")
        req = urllib.request.Request(
            BASE_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                intent = data.get("intent")
                sources = data.get("sources", [])
                answer = data.get("answer", "")

                print(f"-> Returned Intent: {intent}")
                print(f"-> Sources Count: {len(sources)}")
                
                # Check criteria
                has_web_sources = any(s.get("source_type") == "web" or "url" in s for s in sources)
                print(f"-> Has Web Sources & URLs: {has_web_sources}")
                if sources:
                    print(f"-> Top Source Title: {sources[0].get('title')}")
                    print(f"-> Top Source URL: {sources[0].get('url', '')[:65]}...")
                
                print(f"-> Answer Preview:\n{answer[:200]}...")

                if intent == test["expect_intent"] and len(sources) > 0 and has_web_sources and answer:
                    print(f"✅ PASSED: {test['name']}")
                    passed += 1
                else:
                    print(f"❌ FAILED: {test['name']}")
                    failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Summary: {passed} Passed, {failed} Failed out of {len(TESTS)} tests")
    print("=" * 70 + "\n")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
