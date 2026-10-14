# Execution environments

Execution environments package Ansible, collections, Python dependencies, and
system dependencies into container images. AAP runs automation jobs in these
images; CLI users can also use them through tools such as `ansible-navigator`.

## Choose a runtime

Use an existing image when it supplies the demo's tested dependencies. Document
its registry location and tested tag or digest in the demo README.

When a custom image is needed, retain the demo's `execution-environment/`
directory and update its Ansible Builder definition:

- Replace the placeholder base image with a suitable, accessible image.
- Pin collection versions in `collections/requirements.yml`.
- Add Python dependencies to `requirements.txt`.
- Add system dependencies to `bindep.txt`.

The starter definition uses Ansible Builder schema version 3. It is a template
and requires a real base image before building.

## Build and publish

With a compatible Ansible Builder installation and container engine, run from
the selected demo's execution environment directory:

```bash
cd demos/<demo-name>/execution-environment
ansible-builder build --file execution-environment.yml \
  --tag <registry>/<namespace>/<image>:<version>
```

Push the image using your container engine, register it in AAP, and select it for
the demo's job templates. Document registry authentication separately from
credentials used by the playbook.

Reference the same collection requirements file for CLI installation and image
builds. Test both execution modes when advertising support for both. Create shared
runtime definitions later if several demos need the same dependencies.

See the [Ansible Builder documentation](https://ansible.readthedocs.io/projects/builder/en/stable/)
for definition syntax and build prerequisites.
