
# CloudLab provider configuration, specifying the path to the credentials file and API endpoint
terraform {
  required_providers {
    cloudlab = {
      source  = "pgrigo01/cloudlab" # this directory is under the .terraform directory
      version = "5.0.0" 
    }
  }
}

provider "cloudlab" {
  project          = "UCY-CS499-DC"
  credentials_path = "cloudlab-decrypted.pem"
}

resource "cloudlab_simple_experiment" "vm1"{
    name = "experiment1"
    routable_ip = true
    image        = "UBUNTU 22.04"
    aggregate    = "emulab.net"
}
