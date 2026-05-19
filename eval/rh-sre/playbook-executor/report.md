# A/B Evaluation Report: rh-sre-playbook-executor

## Summary

* Related PR: https://github.com/RHEcosystemAppEng/skill-submissions/pull/12
* LLM: Claude Sonnet 4.6 (vertex_ai)

| Metric | Treatment | Control |
|--------|-----------|---------|
| Trials | 3 | 3 |
| Passed | 3 | 3 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Pass Rate | 1.0000 | 1.0000 |
| Mean Reward | 1.0000 | 0.6667 |
| Median Reward | 1.0000 | 0.7143 |
| Std Reward | 0.0000 | 0.0825 |

## Comparison

- **Mean reward gap (Uplift):** +0.3333
- **Welch's t-test p-value:** 0.0198
- **Fisher's exact p-value:** 1.0000
- **Recommendation:** **PASS**

## Provenance

- Generated at: 2026-05-18T13:52:34.630588Z
- Commit SHA: `12a2604c692c9a1ba53795bac0f6443b5d8fa12e`
- Pipeline run: `abevalflow-xsgvd`
- Treatment image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-playbook-executor@sha256:e2070114c918dc238d8d0bab8b94f42b8eb4bce45da183b9039bceb167459e7a`
- Control image: `image-registry.openshift-image-registry.svc:5000/ab-eval-flow/rh-sre-playbook-executor@sha256:d372f03bdd293eb8f8e7eefbc1a30b2d0cb9f2cd690a82bdd206f1d5bfa0de07`
- Harbor fork revision: `main`

## Trial Details

<details>
<summary>Treatment (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-playbook-executor__5iDNAnf | 1.0000 | PASS |
| 2 | rh-sre-playbook-executor__SBJ4ahC | 1.0000 | PASS |
| 3 | rh-sre-playbook-executor__bgyXLhp | 1.0000 | PASS |

</details>

<details>
<summary>Control (3 trials)</summary>

| # | Trial | Reward | Passed |
|---|-------|--------|--------|
| 1 | rh-sre-playbook-executor__KE58ibx | 0.7143 | PASS |
| 2 | rh-sre-playbook-executor__VkpRLLc | 0.7143 | PASS |
| 3 | rh-sre-playbook-executor__ww6ryzi | 0.5714 | PASS |

</details>
