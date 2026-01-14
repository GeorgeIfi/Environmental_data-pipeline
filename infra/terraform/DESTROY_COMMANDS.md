# Quick destroy commands

# Option 1: Force destroy (removes prevent_destroy protection)
terraform destroy -auto-approve

# Option 2: If storage account is locked, first empty it manually:
# az storage blob delete-batch --account-name <storage_account_name> --source '$root' --auth-mode login
# Then run: terraform destroy -auto-approve

# Option 3: Target specific resources first:
# terraform destroy -target=azurerm_synapse_workspace.main -auto-approve
# terraform destroy -target=azurerm_data_factory.main -auto-approve  
# terraform destroy -auto-approve