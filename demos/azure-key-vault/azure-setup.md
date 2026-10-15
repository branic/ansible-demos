# Prepare Azure Key Vault

Run these Bash commands with Azure CLI in a lab subscription. They create a
dedicated resource group, a Standard Key Vault, and a Microsoft Entra application
and service principal (the demo's service account). Key Vault operations incur
Azure charges. Use a unique vault name and keep the resource identifiers for
cleanup. Never place the generated client secret in Git.

Prerequisites: permission to create resource groups and vaults, create Entra app
registrations/service principals, and assign Azure roles at the vault scope.
For example, subscription Owner can provision resources and assign roles;
Entra application creation rights are separate. The commands assume an
interactive user login in Azure public cloud.

## Create the vault

Replace the subscription ID and vault name before running:

```bash
az login
az account set --subscription '<subscription-id>'

demo_resource_group='rg-aap-keyvault-demo'
demo_location='eastus'
demo_vault_name='<globally-unique-vault-name>'

az group create --name "$demo_resource_group" --location "$demo_location"
az keyvault create \
  --name "$demo_vault_name" \
  --resource-group "$demo_resource_group" \
  --location "$demo_location" \
  --sku standard \
  --enable-rbac-authorization true \
  --enable-purge-protection true \
  --retention-days 7

demo_vault_id=$(az keyvault show --name "$demo_vault_name" \
  --resource-group "$demo_resource_group" --query id --output tsv)
demo_vault_url=$(az keyvault show --name "$demo_vault_name" \
  --resource-group "$demo_resource_group" --query properties.vaultUri --output tsv)
printf 'vault_url: %s\n' "$demo_vault_url"
```

Vault names must be globally unique, 3–24 characters, begin with a letter,
end with a letter or digit, and contain only letters, digits, and hyphens
(no consecutive hyphens). This lab uses the default public endpoint; Azure
Policy or vault firewalls may require additional networking setup. For a
private endpoint, provide DNS and routing from the controller and setup client.

Microsoft's [Key Vault CLI quickstart](https://learn.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli)
describes vault provisioning and secret operations. This demo explicitly uses
Azure RBAC rather than legacy vault access policies.

## Allow the setup user to populate secrets

Resource management permissions do not automatically grant secret data access.
Assign the signed-in user **Key Vault Secrets Officer** at this vault only:

```bash
demo_operator_id=$(az ad signed-in-user show --query id --output tsv)
az role assignment create \
  --assignee-object-id "$demo_operator_id" \
  --assignee-principal-type User \
  --role 'Key Vault Secrets Officer' \
  --scope "$demo_vault_id"
```

Wait for role propagation before setting secrets. If a secret command returns
403 immediately after a role assignment, wait several minutes and retry that
command. Do not recreate the application or vault to resolve propagation delay.

## Create the service account and grant read access

```bash
az ad sp create-for-rbac --name "aap-keyvault-demo-$demo_vault_name" --years 1
```

Current Azure CLI creates the application and service principal without a role
assignment unless a role/scope is supplied. The output contains `appId`,
`password`, and `tenant`. Save them in a password manager for the AAP source
credential: `appId` is Client ID, `password` is Client Secret, and `tenant` is
Tenant ID. The client secret value is returned at creation; an Azure portal
secret ID is not a substitute. See the official
[service principal command reference](https://learn.microsoft.com/en-us/cli/azure/ad/sp#az-ad-sp-create-for-rbac).

Set the non-secret application ID, then grant secret read access:

```bash
demo_client_id='<appId-from-the-previous-command>'
demo_sp_object_id=$(az ad sp show --id "$demo_client_id" --query id --output tsv)
az role assignment create \
  --assignee-object-id "$demo_sp_object_id" \
  --assignee-principal-type ServicePrincipal \
  --role 'Key Vault Secrets User' \
  --scope "$demo_vault_id"
```

If the new service principal is not yet visible, retry `az ad sp show` after
directory propagation. The service principal can read secrets in this dedicated
vault; it does not receive permissions to write secrets or manage Azure
resources. The setup user's Secrets Officer role is separate. See Microsoft's
[Key Vault RBAC guide](https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide)
for the data access roles.

## Populate the two secrets

These are disposable demonstration strings, not credentials to a real system:

```bash
az keyvault secret set --vault-name "$demo_vault_name" \
  --name demo-username --value 'keyvault-demo-user' --output none
az keyvault secret set --vault-name "$demo_vault_name" \
  --name demo-password --value 'KeyVault-demo-only-password-1!' --output none
```

Store each value as its own secret, not as a single JSON document. Continue with
[AAP configuration](aap/README.md), using the vault URL and generated service
principal credentials. Test both lookups in AAP to verify the service account's
access; reading secrets as your setup user only tests your user's permissions.

## Verify and rotate

Inspect secret metadata as the setup user without printing the password:

```bash
az keyvault secret show --vault-name "$demo_vault_name" \
  --name demo-username --query '{id:id,enabled:attributes.enabled}' --output json
az keyvault secret show --vault-name "$demo_vault_name" \
  --name demo-password --query '{id:id,enabled:attributes.enabled}' --output json
```

After the first successful AAP job, create another username version:

```bash
az keyvault secret set --vault-name "$demo_vault_name" \
  --name demo-username --value 'keyvault-demo-user-v2' --output none
```

Launch a new AAP job. A field lookup with blank Secret Version uses the latest
version. Restore the initial username by running the original secret-set
command if desired. The password can be rotated the same way.

## Cleanup Azure resources

First remove the AAP objects as described in the [demo README](README.md#cleanup).
Keep the same shell variables or restore the identifiers recorded during setup.
The following commands delete the dedicated demo resource group and demo app;
confirm both identifiers refer to resources created for this demo.

```bash
az group delete --name "$demo_resource_group" --yes
az ad app delete --id "$demo_client_id"
```

Deleting the resource group removes the vault and its scoped role assignments.
The application registration is tenant-wide and requires separate deletion;
deleting it also removes its service principal. Verify resource removal:

```bash
az group exists --name "$demo_resource_group"
az ad app show --id "$demo_client_id"
az ad sp show --id "$demo_client_id"
az keyvault list-deleted --query "[?name=='$demo_vault_name'].name" --output tsv
```

Expect `false` for the group, not-found errors for the app and service principal,
and the vault in the soft-deleted list. Purge protection retains the deleted
vault for the configured seven days and prevents immediate name reuse. Use a
new vault name for an immediate rebuild. See the
[soft-delete overview](https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview)
for retention and recovery behavior.
