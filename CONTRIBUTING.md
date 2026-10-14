# Contributing demos

## Create a demo

From the repository root:

```bash
cp -R templates/demo demos/<demo-name>
```

Use a descriptive, lowercase name with hyphens. Organize demos by subject rather
than separating them into CLI and AAP directories.

Replace the template instructions and starter tasks with the actual demo. Remove
unused directories, including `aap/` for CLI-only demos and custom execution
environment files when an existing image provides the required runtime.

## Document execution

- Declare CLI, AAP, or both, and record the versions tested for each mode.
- Use the same playbooks for both modes when the automation is the same.
- Document commands from the repository root and AAP playbook paths relative to
  that root.
- List inputs, defaults, credential sources, expected results, and cleanup.
- For AAP, describe project, inventory, credential, execution environment, job
  template, survey, and workflow configuration as applicable.
- Describe any automated AAP configuration and how to apply and remove it.

Keep credentials and environment-specific values out of committed examples.
Pin dependency versions to those validated for the demo. Keep roles next to the
playbooks that use them, under `playbooks/roles/`; the template's `roles/` directory
documents external role dependencies when needed.

## Validate and publish

Every demo must pass the ansible-lint **production** profile. The root
`.ansible-lint` configuration selects this profile and treats warnings as
failures. It applies to CLI-only, AAP-only, and dual-mode demos, including their
Ansible-based AAP configuration. Keep rules enabled; do not add rule skips,
ignore entries, or `noqa` annotations to make a failing demo pass.

Install the repository's pinned lint tooling in a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

1. Install the demo's documented collection and role dependencies into the lint
   environment. Put collection requirements in `collections/requirements.yml` and
   external role requirements in `roles/requirements.yml` within the demo.
   Runtime images alone do not make their collections available to a host linter.
2. From the repository root, run the production lint check:

   ```bash
   ansible-lint --offline --config-file .ansible-lint demos/<demo-name>
   ```

   Use `templates/demo` instead to validate the starter. Offline mode prevents
   implicit downloads during linting; install dependencies before running it.
3. Run syntax checks for each playbook, for example:

   ```bash
   ansible-playbook -i demos/<demo-name>/inventory/hosts.yml \
     demos/<demo-name>/playbooks/demo.yml --syntax-check
   ```

4. Run the full demo and verify its results in each advertised execution mode.
5. Run cleanup and verify that the documented resources are removed.
6. Record tested versions and limitations in the demo README.
7. Add a linked entry to the root README's demo catalog.

The `Ansible lint` GitHub Actions workflow automatically discovers every demo
directory directly under `demos/` and also validates `templates/demo`. Each runs
in a separate job with its own dependencies, so demos can pin different versions.
Checks run on pushes and pull requests. If a demo needs additional tooling or
private dependencies for linting, provide that setup in the workflow before
publishing it. Never bypass missing dependencies with mocked modules or roles.

Configure repository branch protection or a ruleset to require the stable
`Production lint` status check before merging. This final job fails if discovery
or any demo's lint job fails or is skipped.

Do not label an execution mode as supported based solely on lint or syntax checks.
