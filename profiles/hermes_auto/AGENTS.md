# AEC Hermes automatic-cycle policy

This directory is the isolated workspace for the explicitly selected
Hermes-driven automatic presentation mode. It is separate from the repository
root's human-gated manual policy.

- The human operator's deliberate launch of
  `scripts/start-portable-auto-hermes-demo.sh` authorizes exactly one complete
  Phase 2-12 cycle through the checked deterministic adapter runner.
- This is launch authorization, not a phase approval. Never generate, quote,
  simulate, or request the manual mode's approval language.
- Use only the terminal tool and only the exact authorized wrapper command in
  the supplied user message. The launcher already verifies that wrapper; do
  not inspect or list it. Start it once with `background=true` and
  `notify_on_complete=true`.
- Repeatedly use blocking process `wait` calls at the presentation interval
  supplied in the user message until the process exits. A wait timeout means
  report newly visible markers briefly and wait again; it is not a failure.
  Never restart the process, use process poll/log, or inspect the wrapper.
- Report only new wrapper-produced facts. Never infer checks, phases, files, or
  work that its output does not contain. `HERMES_AUTO_DRY_RUN_OK` is a
  successful launcher test in which zero demonstration phases ran.
- Do not read files, edit files, invoke raw MCP methods, download assets, or run
  alternative terminal commands.
- Briefly identify Hermes and the authorized one-cycle scope before invoking
  the wrapper, then wait for it to finish.
- On success, summarize its phase and final-image markers. On failure, report
  the exact failed marker and stop without retries or workarounds.
- Normal Hermes command-safety controls remain active. This mode must never be
  launched with broad approval-bypass or rule-bypass flags.
