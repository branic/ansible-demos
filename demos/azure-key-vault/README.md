# Azure Key Vault credentials

Demonstrate AAP retrieving a username and password from Azure Key Vault through
the built-in **Microsoft Azure Key Vault** credential type. A custom credential
has two required inputs, each backed by an external lookup, and injects the
retrieved strings as extra variables into a job. The playbook validates that
both contain data and displays them with `ansible.builtin.debug`.

```text
Azure Key Vault: demo-username + demo-password
  → Microsoft Azure Key Vault source credential (service principal)
  → custom credential: username + password (two input-source mappings)
  → job extra variables
  → validate and display
```

Use disposable secret values: the display task intentionally outputs credentials.
The username is not marked secret in the custom type and should print visibly;
the password is marked secret and AAP can mask it as `********`. This demonstrates
both field settings while validating that the playbook received nonempty strings.

## Execution mode and validation status

**AAP demo, pending Azure and controller lab validation.** Local checks validate
the playbook using synthetic inputs; they do not test the external lookup or
prove AAP credential injection. CLI execution is not an alternative to the AAP
credential integration demonstrated here.

| Component | Requirement / tested version |
| --- | --- |
| AAP | Target 2.6; controller execution pending |
| Azure | Public cloud subscription and Microsoft Entra tenant; provisioning pending |
| Azure CLI | Current CLI with `az keyvault` and `az ad sp`; lab version pending |
| ansible-core | Local playbook verification: 2.20.7 |
| ansible-lint | 26.6.0, production profile (core 2.21.2) |
| Collections | ansible.builtin only; no additional collections |
| Target | localhost inside the job EE; no managed machines |
| Execution environment | AAP-compatible Python 3 / ansible-core EE; image digest pending |

Prerequisites include an AAP administrator able to manage credential types and
credentials, Azure provisioning/app registration/role assignment permissions,
and controller HTTPS access to the vault and Microsoft Entra token endpoints.
The Azure CLI is needed only on the setup workstation or Azure Cloud Shell.
No custom EE build is required.

## Inputs

| Playbook variable | Credential field | Key Vault secret | Default |
| --- | --- | --- | --- |
| `azure_key_vault_demo_username` | `username` | `demo-username` | None; required non-secret string |
| `azure_key_vault_demo_password` | `password` | `demo-password` | None; required secret string |

Only the password is marked secret in the custom type. Both values are stored
as secrets in Azure Key Vault; the custom type controls their treatment in AAP.
Supply neither variable in
inventory nor template extra variables: the custom credential injects them.
The Azure service principal's client secret belongs only in the external source
credential and is never used as the demo's password variable.

## Setup and run

1. Follow [Azure setup](azure-setup.md) to create the vault, service account,
   read permission, and both secrets. These resources incur Azure charges.
2. Follow [AAP configuration](aap/README.md) to create the built-in source
   credential, custom type and credential, two lookups, inventory, and template.
3. Launch **Azure Key Vault - use retrieved credentials** and verify its result.
4. Rotate the username in Key Vault and launch again to demonstrate retrieval
   of the latest version without changing the AAP credential.

## Verify

From the repository root, with the [repository lint tooling](../../CONTRIBUTING.md#validate-and-publish)
installed:

```bash
ansible-lint --offline --config-file .ansible-lint demos/azure-key-vault
ansible-playbook -i demos/azure-key-vault/inventory/demo.yml \
  demos/azure-key-vault/playbooks/demo.yml --syntax-check
```

For a local smoke check of validation and display only, supply synthetic values:

```bash
ansible-playbook -i demos/azure-key-vault/inventory/demo.yml \
  demos/azure-key-vault/playbooks/demo.yml \
  -e '{"azure_key_vault_demo_username":"synthetic-user","azure_key_vault_demo_password":"synthetic-password"}'
```

Expect a successful assertion, a message confirming both values contain data,
and a debug message showing both synthetic strings. Running without either
variable, or with an empty or whitespace-only value, must fail validation before
the display task. The assertion's details are hidden by `no_log`.

For integration verification, run the AAP template with no manually supplied
values. Expect a **Successful** job and the confirmation message. The final
debug task should show the username, while AAP may mask the password. The
lookup tests and a new job after rotation verify the external credential path.
Record the Azure CLI, AAP, and EE versions after completing those lab checks.

## Cleanup

1. Delete the demo job template.
2. Delete **Azure Key Vault demo application** (including its input-source
   mappings), then **Azure Key Vault demo source**.
3. Delete **Azure Key Vault demo username and password** credential type when
   no credentials use it.
4. Remove the demo inventory/source and any project created solely for this
   demo. Preserve shared projects and EEs. Remove retained demo jobs according
   to your lab's job-history policy because stdout may contain demo values.
5. Follow [Azure cleanup](azure-setup.md#cleanup-azure-resources) to delete the
   dedicated resource group and application registration and verify removal.

## Limitations

The playbook demonstrates consumption, not authentication against a real
application. The two secrets are fetched independently; rotation of both is
not an atomic transaction. Blank versions use the latest values at lookup time.
The source credential's client secret expires and must be maintained separately.
See [AAP troubleshooting](aap/README.md#troubleshooting) for lookup failures and
output masking. This demo does not provision resources or controller objects
automatically.
