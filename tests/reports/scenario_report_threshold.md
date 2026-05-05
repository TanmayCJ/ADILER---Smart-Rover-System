# Scenario Test Report

## boulder_field
Status: PASS
Errors:
- None
Threshold Reasoning:
PASS: risk_score=0.5411057692307693 and current_action=moving match expected_risk_level=medium and expected_action=moving.
Next Plan (LLM):
{}

## cliff_edge
Status: FAIL
Errors:
- Risk score 0.54 too low for high/critical scenario.
- Planner decision expected stop/replan but current_action did not reflect it.
- Expected action 'replan_required', got 'moving'.
Threshold Reasoning:
FAIL: risk_score=0.5411057692307693 and current_action=moving did not meet expected_risk_level=high or expected_action=replan_required.
Next Plan (LLM):
{}

## dust_storm
Status: PASS
Errors:
- None
Threshold Reasoning:
PASS: risk_score=0.5411057692307693 and current_action=moving match expected_risk_level=medium and expected_action=moving.
Next Plan (LLM):
{}
