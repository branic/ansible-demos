# Ansible Demos

A collection of practical demonstrations for Ansible CLI and Red Hat Ansible
Automation Platform (AAP).

Each demo documents its supported execution methods, prerequisites, tested
versions, setup, expected results, and cleanup.

## Demo catalog

Each demo declares one of these execution modes:

- **CLI** — Run from the command line.
- **AAP** — Run through Ansible Automation Platform.
- **Both** — Includes tested instructions for CLI and AAP execution.

| Demo | Description | Execution mode |
| --- | --- | --- |
| [Workflow host failure](demos/workflow-host-failure/README.md) | Rescue task failures and skip those hosts in later AAP jobs. | AAP (controller validation pending); CLI verification included |

## Getting started

1. Choose a demo and check its supported execution modes.
2. Read its README for prerequisites and tested versions.
3. Prepare the required lab environment.
4. Follow the CLI or AAP instructions.
5. Verify the results and complete the cleanup steps.

### Running with the CLI

Follow the demo's dependency installation, inventory configuration, and playbook
execution instructions. Run commands from the repository root unless documented
otherwise.

See [Running with CLI](docs/running-with-cli.md) for shared guidance.

### Running with AAP

Follow the demo's AAP instructions to configure its project, execution environment,
inventory, credentials, and job or workflow templates.

See [Running with AAP](docs/running-with-aap.md) for shared guidance.

## Repository layout

```text
ansible-demos/
├── README.md
├── CONTRIBUTING.md
├── ansible.cfg
├── docs/
│   ├── running-with-cli.md
│   ├── running-with-aap.md
│   └── execution-environments.md
├── templates/
│   └── demo/
│       ├── README.md
│       ├── playbooks/
│       ├── inventory/
│       ├── vars/
│       ├── collections/
│       ├── roles/
│       ├── execution-environment/
│       └── aap/
│           └── configuration/
└── demos/
```

- `demos/` — Published demo content and instructions.
- `docs/` — Shared setup and execution guidance.
- `templates/demo/` — Starter files to copy when creating a demo. Remove optional
  files and directories that the demo does not need.
- `ansible.cfg` — Minimal defaults shared by CLI and AAP playbook execution.

## Demo requirements

Every demo must document:

- Purpose and expected outcome.
- Supported execution modes: CLI, AAP, or both.
- Tested Ansible, AAP, collection, and target platform versions, as applicable.
- Required infrastructure, permissions, and credentials.
- Dependencies and execution environment requirements.
- A passing ansible-lint production profile check, with warnings treated as failures.
- Inputs, setup, execution, and verification.
- Cleanup steps and any infrastructure costs.

AAP-supported demos must also document template configuration, including playbook
paths, inventory, credential types, execution environment, variables, and any
surveys or workflow relationships.

## Contributing

Use `templates/demo/` as a starting point. Validate every advertised execution
mode and add the demo to the catalog. Every demo and the starter template must
pass the repository's ansible-lint production configuration; GitHub Actions checks
each one separately on pushes and pull requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Credentials and lab safety

Review inventory targets and resource changes before execution. Use lab
environments and complete the documented cleanup.

Never commit passwords, tokens, private keys, or decrypted secrets. Use
placeholder values in examples and document how credentials should be supplied.

## License

A repository license has not been selected yet.
