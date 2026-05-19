# A/B Evaluation Report: ocp-admin-cluster-creator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/27
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.1667 |
| Median Reward | 1.0000 | 0.1667 |
| Std Reward | 0.0000 | 0.0000 |

## Comparison

- **Mean reward gap (Uplift):** +0.8333
- **Welch's t-test p-value:** 0.0000
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-18T16:06:15.130817Z
- Commit SHA: `b0bca9625b7e32d1faf3c12aa9c93aaad3b19758`
- Pipeline run: `abevalflow-xtjrr`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-creator@sha256:4b09ecdb7a0bf710d96cc19ac8043765c83d59a8d409ead6d51cf0cfe23998ce`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/ocp-admin-cluster-creator@sha256:83523e19c6207b1093310d8352e12a2bb5fcb765e47e3ccd9a618a663950d1d7`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-creator__LwzDeWY | 1.0000 | PASS |
| 2 | ocp-admin-cluster-creator__pWmRWch | 1.0000 | PASS |
| 3 | ocp-admin-cluster-creator__w2pwYod | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | ocp-admin-cluster-creator__FDZdSFV | 0.1667 | PASS |
| 2 | ocp-admin-cluster-creator__ZRRDuvm | 0.1667 | PASS |
| 3 | ocp-admin-cluster-creator__z49cZmG | 0.1667 | PASS |

</details>
