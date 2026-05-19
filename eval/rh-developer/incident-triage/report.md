# A/B Evaluation Report: rh-developer-incident-triage

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/54
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.9375 |
| Median Reward | 1.0000 | 0.9375 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.0625
- **Welch's t-test p-value:** 0.0000
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-12T20:17:14.650537Z
- Commit SHA: `fa0b4ba60a089a7f50001993e2fbeb199db2ad8b`
- Pipeline run: `abevalflow-r9hxr`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-incident-triage@sha256:ea9e7f972dfa3f03b927e88d8a0f816f15058ed5b6a22d80d32eec680f3cccff`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-incident-triage@sha256:0e4f31dde9ad9e924cfd7bbc80c60e256a85626e795f384a0359125772b01bcd`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-incident-triage__SpBpgXG | 1.0000 | PASS |
| 2 | rh-developer-incident-triage__VDPyd6j | 1.0000 | PASS |
| 3 | rh-developer-incident-triage__etQfpHW | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-incident-triage__LeJEZSc | 0.9375 | PASS |
| 2 | rh-developer-incident-triage__QNoqSYb | 0.9375 | PASS |
| 3 | rh-developer-incident-triage__YRPotaM | 0.9375 | PASS |

</details>
