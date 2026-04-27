#!/bin/bash

pip3 install --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5 \
    anthropic>=0.75.0

TEST_FILE=$(find / -name "test_outputs.py" 2>/dev/null | head -1)
JUDGE_FILE=$(find / -name "llm_judge.py" 2>/dev/null | head -1)

if [ -z "$TEST_FILE" ]; then
    echo "ERROR: Could not find test_outputs.py"
    echo "0" > /logs/verifier/reward.txt
    exit 1
fi

echo "=== Files created by agent in /root ==="
ls -la /root/*.md 2>/dev/null || echo "No markdown files found"

echo ""
echo "════════════════════════════════════════════"
echo "  Phase 1: Deterministic Tests (pytest)"
echo "════════════════════════════════════════════"

pytest "$TEST_FILE" \
    --ctrf=/logs/verifier/ctrf.json \
    -v 2>&1

pytest_exit=$?

pytest_passed=0
pytest_total=0
if [ -f /logs/verifier/ctrf.json ]; then
    pytest_passed=$(python3 -c "import json; d=json.load(open('/logs/verifier/ctrf.json')); print(d['results']['summary']['passed'])" 2>/dev/null)
    pytest_total=$(python3 -c "import json; d=json.load(open('/logs/verifier/ctrf.json')); print(d['results']['summary']['tests'])" 2>/dev/null)
fi
echo "=== Pytest: ${pytest_passed}/${pytest_total} passed ==="

echo ""
echo "════════════════════════════════════════════"
echo "  Phase 2: LLM Judge (skill evaluation)"
echo "════════════════════════════════════════════"

llm_passed=0
llm_total=0

if [ -n "$JUDGE_FILE" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
    timeout 180 python3 "$JUDGE_FILE"

    if [ -f /logs/verifier/llm_judge.json ]; then
        llm_passed=$(python3 -c "import json; d=json.load(open('/logs/verifier/llm_judge.json')); print(d['passed'])" 2>/dev/null)
        llm_total=$(python3 -c "import json; d=json.load(open('/logs/verifier/llm_judge.json')); print(d['total'])" 2>/dev/null)
    fi
    echo "=== LLM Judge: ${llm_passed}/${llm_total} passed ==="
else
    if [ -z "$JUDGE_FILE" ]; then
        echo "WARNING: llm_judge.py not found, skipping LLM evaluation"
    fi
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "WARNING: ANTHROPIC_API_KEY not set, skipping LLM evaluation"
    fi
fi

echo ""
echo "════════════════════════════════════════════"
echo "  Combined Score"
echo "════════════════════════════════════════════"

reward=$(python3 -c "
pytest_p = int('${pytest_passed}' or 0)
pytest_t = int('${pytest_total}' or 0)
llm_p = int('${llm_passed}' or 0)
llm_t = int('${llm_total}' or 0)
total_p = pytest_p + llm_p
total_t = pytest_t + llm_t
reward = round(total_p / total_t, 4) if total_t > 0 else 0.0
print(reward)
" 2>/dev/null)

echo "$reward" > /logs/verifier/reward.txt
echo "=== Final Reward: $reward (pytest=${pytest_passed}/${pytest_total} + llm=${llm_passed}/${llm_total}) ==="

cp /root/*.md /logs/verifier/ 2>/dev/null || true

exit 0
