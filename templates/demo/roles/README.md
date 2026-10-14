# Role dependencies

If external roles are needed, add a `requirements.yml` here with tested version
pins. Document an explicit CLI installation command and how the execution
environment provides those roles for AAP. This nested directory is not
automatically processed by controller project synchronization.

Place demo-local role implementations in `playbooks/roles/` so playbooks can
discover them without depending on the current working directory.

Remove this directory if the demo does not use external roles.
