# Configure Azure Key Vault credentials in AAP

Use AAP 2.6 or later.
Complete [Azure setup](../azure-setup.md) first. These steps create AAP objects
manually; the configuration YAML files are UI snippets, not playbooks.

## Create the external source credential

Under **Automation Execution → Infrastructure → Credentials**, create:

| Setting | Value |
| --- | --- |
| Name | Azure Key Vault demo source |
| Organization | Your demo organization |
| Credential type | **Microsoft Azure Key Vault** |
| Vault URL (DNS Name) | `vault_url` from Azure setup, such as `https://your-vault.vault.azure.net/` |
| Client ID | Service principal `appId` |
| Client Secret | Service principal `password` (the client secret value) |
| Tenant ID | Service principal `tenant` |
| Cloud Environment, if shown | Azure public cloud / `AzureCloud` |

The client secret authenticates AAP to Azure. It is separate from the demo
password stored inside Key Vault. Use the built-in Key Vault type, rather than
the Microsoft Azure Resource Manager credential type.

See the upstream [Key Vault credential documentation](https://docs.ansible.com/projects/awx/en/24.6.1/userguide/credential_plugins.html#microsoft-azure-key-vault)
for the source credential fields.

## Create the custom type

As an automation controller administrator with permission to manage credential
types, open **Automation Execution → Infrastructure → Credential Types** and
create **Azure Key Vault demo username and password**:

- Input Configuration: paste [credential-type-inputs.yml](configuration/credential-type-inputs.yml).
- Injector Configuration: paste [credential-type-injectors.yml](configuration/credential-type-injectors.yml).

Both string fields are required. Username has `secret: false` so its value can
be displayed; Password has `secret: true` to demonstrate secret masking.
Both values are still retrieved from Azure Key Vault secrets. The injectors map them to
`azure_key_vault_demo_username` and `azure_key_vault_demo_password` as job extra
variables. If reusing a type, verify that its IDs and injectors match these files.
See [custom credential types](https://docs.ansible.com/projects/awx/en/24.6.1/userguide/credential_types.html)
for the input and injector schema.

## Create the credential and link both fields

Create a credential named **Azure Key Vault demo application**, in the demo
organization, using **Azure Key Vault demo username and password**.
For each input, use the external secret lookup/key control next to the field
and select **Azure Key Vault demo source**:

| Custom credential input | Source credential | Secret Name | Secret Version |
| --- | --- | --- | --- |
| Username (`username`) | Azure Key Vault demo source | `demo-username` | Leave blank |
| Password (`password`) | Azure Key Vault demo source | `demo-password` | Leave blank |

Use the secret names, not secret URLs or JSON property paths. Test each lookup
using the UI's test action, then save both mappings and the credential. Do not
paste literal values into these fields. Blank versions request the latest
version; specify a version ID only when intentionally pinning it.
The saved mappings are controller credential input sources: each links one
target field to the source credential and its own lookup metadata.

## Project, inventory, and job template

1. Create or reuse an SCM project for this repository and demo branch, then sync.
2. Create **Azure Key Vault demo** inventory. Add a **Sourced from a Project**
   inventory source using `demos/azure-key-vault/inventory/demo.yml` and sync it.
3. Select an AAP-compatible EE containing ansible-core 2.16+. No Azure
   collections, Azure CLI, or Azure SDK need to be added to the job's EE: the
   controller's credential plugin retrieves the values before the playbook runs.
4. Create the job template below. Give the launching user permission to execute
   the template and use the required credentials, project, inventory, and EE.

| Setting | Value |
| --- | --- |
| Name | Azure Key Vault - use retrieved credentials |
| Job type | Run |
| Project | The synchronized repository project |
| Playbook | `demos/azure-key-vault/playbooks/demo.yml` |
| Inventory | Azure Key Vault demo |
| Execution environment | The selected EE |
| Credentials | **Azure Key Vault demo application** |
| Extra variables | `{}` |
| Surveys and launch prompts | Disabled |
| Privilege escalation | Disabled |
| Fact storage / caching | Disabled |
| Limit, job tags, skip tags | Blank |
| Job slicing | 1 |

Attach the custom application credential to the template. Its field mappings
reference the Key Vault source credential; that source credential is not a
separate job credential. No Machine credential is needed for localhost.
Keep the two injected variable names out of project/inventory variables,
surveys, and template extra variables so the demo exercises credential injection.

## Present and verify

1. Launch **Azure Key Vault - use retrieved credentials** without extra variables.
2. The job should succeed and print the confirmation that both values contain
   data. The final debug task references both injected variables. Expect the
   username `keyvault-demo-user` to be visible because it is not marked secret.
   The password is marked secret and AAP may redact it as `********`; keep
   password masking enabled. If unmasked in a lab, its disposable value is
   `KeyVault-demo-only-password-1!`.
3. To demonstrate retrieval at launch, update `demo-username` using the rotation
   command in [Azure setup](../azure-setup.md#verify-and-rotate), then launch a
   new job without editing the AAP credential. With blank Secret Version, the
   new job should display `keyvault-demo-user-v2` while the password remains
   marked secret.

Only use disposable demo values. The final task deliberately asks Ansible to
display both fields; job output can expose them where masking is not applied.
For real automation, remove that task and use `no_log: true` on tasks consuming
the credentials. Do not encode or transform secrets to bypass AAP masking.

## Troubleshooting

- **Lookup fails before any task starts:** check the source credential's vault
  URL, tenant, client ID, client secret expiry, and both field mappings.
- **Forbidden / 403:** verify the service principal has **Key Vault Secrets
  User** at this vault's scope. Subscription Contributor or Key Vault Reader
  alone cannot read secret values. Allow time for RBAC propagation.
- **Timeout / network denial:** the controller component performing the lookup
  must resolve and reach the vault and Microsoft Entra token endpoints over
  HTTPS. EE connectivity alone does not establish controller connectivity.
- **Secret not found:** verify the exact secret name, enabled state, and any
  pinned version. Clear Secret Version to retrieve the latest version.
- **Assertion fails:** confirm the custom credential is attached, both lookups
  are saved, the injector variable names match, and neither secret is blank.
  The validation task uses `no_log` so failed checks do not print secret data.
- **Username is masked:** check that the custom type's `username` field has
  `secret: false`, including when updating an existing type.
- **Password is masked:** this is expected for `secret: true`. Successful
  validation still shows that both strings contain data.

See the [demo README](../README.md#cleanup) for removal steps.
