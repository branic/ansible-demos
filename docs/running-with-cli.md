# Running with the CLI

Each demo README is the authority for its commands and supported versions. The
examples below use `<demo-name>` as a placeholder and run from the repository
root so that the shared `ansible.cfg` is used.

## Prepare the environment

Install the Ansible version specified by the demo in an isolated environment, or
use its documented execution environment with `ansible-navigator`.

When a demo declares collection dependencies, install them into your active
Ansible environment:

```bash
ansible-galaxy collection install -r demos/<demo-name>/collections/requirements.yml
```

If the demo declares external roles, follow its role installation instructions.
Install any documented Python and system dependencies when running directly on
the host; installing collections alone does not provide all runtime dependencies.

## Configure and run

When the demo supplies these example files:

```bash
cp demos/<demo-name>/inventory/hosts.yml.example demos/<demo-name>/inventory/hosts.yml
cp demos/<demo-name>/vars/demo.yml.example demos/<demo-name>/vars/demo.yml
```

Edit the copies for your lab. They are ignored by Git. Supply secrets through the
credential mechanism documented by the demo.

```bash
ansible-inventory -i demos/<demo-name>/inventory/hosts.yml --graph
ansible-playbook -i demos/<demo-name>/inventory/hosts.yml \
  demos/<demo-name>/playbooks/demo.yml \
  -e @demos/<demo-name>/vars/demo.yml
```

Follow the demo's verification and cleanup steps. Do not assume every demo uses
the same playbook names or input files.
