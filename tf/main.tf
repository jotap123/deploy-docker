terraform {
  backend "azurerm" {
    resource_group_name  = "rg-mlopaes"
    storage_account_name = "testmlopaes"
    container_name       = "terraform"
    key                  = "testmlopaes.terraform.tfstate"
  }
}

resource "azurerm_batch_account" "batch_account" {
  name                 = local.batch_account_name
  resource_group_name  = local.resource_group
  location             = local.location
  pool_allocation_mode = "BatchService"
  tags = {
    environment = "Production"
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_batch_pool" "batch_pool" {
  name                = local.batch_pool_name
  resource_group_name = local.resource_group
  account_name        = azurerm_batch_account.batch_account.name
  display_name        = "Terraformed Batch"
  vm_size             = local.vm_size
  node_agent_sku_id   = "batch.node.ubuntu 20.04"

  auto_scale {
    evaluation_interval = "PT15M"
    formula             = local.autoscale_formula
  }

  storage_image_reference {
    publisher = "microsoft-azure-batch"
    offer     = "ubuntu-server-container"
    sku       = "20-04-lts"
    version   = "latest"
  }

  container_configuration {
    type = "DockerCompatible"
  }
}

# Setup resource names and other params
locals {
  app_name            = "testbatch"
  group_name          = "MLOpaes (Dev)"
  resource_group      = "rg-mlopaes"
  location            = "eastus2"
  batch_account_name  = "mlopaesbatch"
  batch_pool_name     = "batchpool"
  acr_name            = "54e5ef7c9fb5461ba8e5bfdfb25ddb7d"
  vm_size             = "Standard_D2_v3"
  app_storage_account = "testmlopaes"
  app_container       = "testing"
  virtual_network     = "vnet-test"
  subnet              = "default"
  autoscale_formula   = file("${path.module}/autoscale.txt")
}