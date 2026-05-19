# A/B Evaluation Report: rh-automation-forensic-troubleshooter

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/64
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8667 | 0.3333 |
| Median Reward | 0.8000 | 0.4000 |
| Std Reward | 0.1155 | 0.1155 |

## Comparison

- **Mean reward gap (Uplift):** +0.5333
- **Welch's t-test p-value:** 0.0048
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-17T13:16:07.741796Z
- Commit SHA: `0980debf930ec829f04a9a6db23d85e7928867c4`
- Pipeline run: `abevalflow-nlph9`
