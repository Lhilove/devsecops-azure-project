variable "resource_group_name" {
  default = "devsecops-rg"
}

variable "location" {
  default = "southafricanorth"
}

variable "acr_name" {
  default = "devsecopsakr123"
}

variable "aks_cluster_name" {
  default = "devsecops-aks"
}

variable "node_count" {
  default = 1
}

variable "vm_size" {
  default = "Standard_B2s_v2"
}