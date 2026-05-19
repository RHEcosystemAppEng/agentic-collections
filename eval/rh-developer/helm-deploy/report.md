# A/B Evaluation Report: rh-developer-helm-deploy

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/48
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8571 | 0.5238 |
| Median Reward | 0.8571 | 0.4286 |
| Std Reward | 0.0000 | 0.1649 |

## Comparison

- **Mean reward gap (Uplift):** +0.3333
- **Welch's t-test p-value:** 0.0728
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-18T21:25:44.123953Z
- Commit SHA: `4506aae0a20907312bee348721c9b7e9516773c2`
- Pipeline run: `abevalflow-j5drx`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-helm-deploy@sha256:7bbd04fa7a8a9b93c45cbf8ee03a1e9f9cf3870feddd10a5b41b2e67b3184ebf`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-helm-deploy@sha256:d21230eed7d3d55bb7832772e889396b6261940074ab3ce46082dce89b5945e3`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-helm-deploy__WiSWNrk | 0.8571 | PASS |
| 2 | rh-developer-helm-deploy__Y3kL9xu | 0.8571 | PASS |
| 3 | rh-developer-helm-deploy__ZQ5SJ38 | 0.8571 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-helm-deploy__Aqj75JA | 0.7143 | PASS |
| 2 | rh-developer-helm-deploy__XoZnTAg | 0.4286 | PASS |
| 3 | rh-developer-helm-deploy__n5GYfPr | 0.4286 | PASS |

</details>
