# A/B Evaluation Report: rh-sre-job-template-creator

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/20
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.9091 |
| Median Reward | 1.0000 | 0.9091 |
| Std Reward | 0.0000 | 0.0909 |

## Comparison

- **Mean reward gap (Uplift):** +0.0909
- **Welch's t-test p-value:** 0.2254
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-18T14:34:37.162282Z
- Commit SHA: `7b7a3dda247588b12688d6bc86b54d7d94e93adc`
- Pipeline run: `abevalflow-mq8zs`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-job-template-creator@sha256:c733ee25b3a5e6ac3ad6da74176a946ffb7109bab76b485c665cdce3cf0aed43`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-job-template-creator@sha256:6ae0300fdfb712393cfe247ed38df50ec161239b364a6e7c4539b37e8e24b2c6`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-job-template-creator__L2Ef3WB | 1.0000 | PASS |
| 2 | rh-sre-job-template-creator__VjXuvVj | 1.0000 | PASS |
| 3 | rh-sre-job-template-creator__tAztzdR | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-job-template-creator__77NtAMq | 1.0000 | PASS |
| 2 | rh-sre-job-template-creator__8Vh9WYF | 0.9091 | PASS |
| 3 | rh-sre-job-template-creator__Pf4JkKk | 0.8182 | PASS |

</details>
