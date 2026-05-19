# A/B Evaluation Report: rh-ai-engineer-model-monitor

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/56
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8889 | 0.3333 |
| Median Reward | 1.0000 | 0.3333 |
| Std Reward | 0.1924 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.5556
- **Welch's t-test p-value:** 0.0377
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-17T20:58:32.226928Z
- Commit SHA: `a51a1b1335aa29eb3eecec82371cc4497a62a7d5`
- Pipeline run: `abevalflow-rqj4r`
