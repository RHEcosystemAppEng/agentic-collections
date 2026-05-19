# A/B Evaluation Report: rh-developer-containerize-deploy

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/42
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 0.8333 | 0.7083 |
| Median Reward | 0.8750 | 0.7500 |
| Std Reward | 0.0722 | 0.0722 |

## Comparison

- **Mean reward gap (Uplift):** +0.1250
- **Welch's t-test p-value:** 0.1012
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-17T09:00:02.231539Z
- Commit SHA: `ec6a594b78cf0c1549d0e8807ef49be18faa4f2e`
- Pipeline run: `abevalflow-2ns2h`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-containerize-deploy@sha256:13b87afc832876f6d36f3a3ab3e79a20cb3843b7757c662330f55052dfc1c150`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-developer-containerize-deploy@sha256:bd5b892387d2462bd42ef979a450549dbbbcc6943269edbf075b88ddb2d09421`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-containerize-deploy__QThWs3h | 0.8750 | PASS |
| 2 | rh-developer-containerize-deploy__cZ3EwGF | 0.8750 | PASS |
| 3 | rh-developer-containerize-deploy__zzV3cXD | 0.7500 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-developer-containerize-deploy__RXc4sbK | 0.6250 | PASS |
| 2 | rh-developer-containerize-deploy__kV5AJhh | 0.7500 | PASS |
| 3 | rh-developer-containerize-deploy__sharKSy | 0.7500 | PASS |

</details>
