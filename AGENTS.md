# Documentation standards

Apply these standards to documentation throughout this repository. Follow
[CONTRIBUTING.md](CONTRIBUTING.md) for the contribution and validation workflow.

## Tone and scope

- Use a professional, instructive tone with direct statements and active voice.
- Include information needed to understand, configure, run, and clean up a demo.
  Remove fluff, repetition, obvious explanations, and unrelated implementation details.
- Describe current behavior. Omit development history, earlier revisions,
  validation narratives, lab job IDs, and recorded execution timings.
- Keep limitations brief and actionable. Explain a detail only when it affects
  how the reader uses the demo.

## Requirements and versions

- State the minimum useful Ansible requirement, such as `2.16+`, when the demo
  uses broadly supported features. Avoid inventories of exact tested versions.
- Document a common Ansible requirement for CLI and execution environment (EE)
  use, and keep their versions aligned.
- Use major.minor versions for AAP: `2.7`, not `2.7.20261019`.
- Omit Python, OS, lint runtime, automation controller, and container build
  versions unless they are necessary to run the demo or explain a compatibility
  requirement. Keep exact dependency pins in requirement and build files.
- List collections as **None** when no additional collections need installation.
  Do not present `ansible.builtin` as an external dependency.
- List target inventory groups, hosts, or aliases directly. Avoid explanations
  of where aliases execute unless the reader needs that information.
- Document required network access, infrastructure, permissions, and credential
  sources. Use placeholders for environment-specific values and never include secrets.

## Content placement

- Keep the demo README focused on purpose, execution modes, requirements,
  inputs, commands, expected results, cleanup, and relevant limitations.
- Put AAP configuration in the demo's `aap/README.md` and role interfaces in
  the role's README. Link to these documents instead of repeating their content.
- Link the role README for inputs and outputs without naming internal variables
  in the surrounding prose. Show an internal variable only when the reader must
  use it directly in a documented command or integration.
- Link shared setup and contribution guides instead of duplicating them.

## Accuracy and verification

- Use precise subjects: inventory defines configuration and per-host values;
  playbooks execute tasks. Do not say that inventory runs a command.
- Match instructions and expected results to the current code. Distinguish
  intentional failures from errors that prevent the demo from working.
- Keep verification sections to commands and observable outcomes. Omit lengthy
  test coverage descriptions, acceptance matrices, and evidence summaries.
- Do not claim runtime support based only on lint or syntax checks. State any
  execution-mode limitation briefly without adding a validation history.
- For documentation-only edits, check local links, anchors, commands, and
  formatting. Run runtime checks when a behavior change requires them.

## Formatting and examples

- Use relative links for repository content and descriptive text for external links.
- Show CLI commands from the repository root and AAP playbook paths relative to
  that root. Label any command that requires a different working directory.
- Use tables for requirements and inputs, numbered lists for procedures, and
  fenced code blocks with language identifiers for commands and examples.
- Keep examples runnable and limited to the concepts being demonstrated.
