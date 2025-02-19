terraform {
  required_providers {
    cloudlab = {
      source  = "pgrigo01/cloudlab"
      version = "2.4.2"
    }
  }
}



# CloudLab provider configuration, specifying the path to the credentials file and API endpoint
provider "cloudlab" {
  project          = "UCY-CS499-DC"
  credentials_path = "cloudlab-decrypted.pem"
}

resource "cloudlab_vlan" "my_cloudlab_vlan" {
  name        = "vlan-test"
  subnet_mask = "255.255.255.0"
}

resource "cloudlab_vm" "my_vm" {
  name         = "vmtest5"
  routable_ip  = true
  image        = "UBUNTU 20.04"
  aggregate    = "Any"
}

resource "cloudlab_vm" "my_vm2" {
  name         = "vmtest6"
  routable_ip  = true
  image        = "UBUNTU 20.04"
  aggregate    = "Any"
}