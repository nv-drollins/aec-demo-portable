---
name: skip-portable-blender-animation
description: "Record the intentional canonical Phase 10 animation skip for the still-image demo while preserving the Phase 9 lighting checkpoint. Use only for Phase 10 in AEC_Demo_Portable."
---

# Record the optional animation skip

Phase 10 is optional in the accepted profile. This checked procedure records a
deliberate still-image path without creating camera keyframes or an animation.

## Procedure

- Before approval run only `python3 scripts/check-portable-animation-skip-ready.py`.
- Require `PORTABLE_ANIMATION_SKIP_READY_OK`, then stop with
  `WAITING_FOR_HUMAN_APPROVAL phase=10 name=optional_animation_skip`.
- After one new human approval run only
  `python3 scripts/run-portable-animation-skip.py`.
- Require `PORTABLE_ANIMATION_INPUT_OK`, `PORTABLE_ANIMATION_SKIP_OK`, and
  `PORTABLE_ANIMATION_PREPARATION_OK`.
- Stop with `PHASE_REVIEW_REQUIRED phase=10 name=optional_animation_skipped`.

Do not add keyframes, render animation, alter lighting, or begin Phase 11.
