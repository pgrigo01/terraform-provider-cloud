
# CloudLab provider configuration, specifying the path to the credentials file and API endpoint
terraform {
  required_providers {
    cloudlab = {
      source  = "pgrigo01/cloudlab"
      version = "1.0.3" 
    }
  }
}

provider "cloudlab" {
  project          = "UCY-CS499-DC"
  credentials_path = "cloudlab-decrypted.pem" 
  browser= "chrome" 
}


# resource "cloudlab_simple_experiment" "experiment1"{
#     name = "experiment1"
#     routable_ip = true
#     image        = "UBUNTU 22.04"
#     aggregate    = "emulab.net"
# }


# resource "cloudlab_simple_experiment" "experiment2"{
#     name = "experiment2"
#     routable_ip = true
#     image        = "UBUNTU 22.04"
#     aggregate    = "emulab.net"
# }

# resource "cloudlab_simple_experiment" "experiment3"{
#     name = "vm1"
#     routable_ip = true
#     image        = "UBUNTU 22.04"
#     aggregate    = "emulab.net"
# }


# resource "cloudlab_simple_experiment" "experiment4"{
#     name = "utahexperiment"
#     routable_ip = true
#     image        = "UBUNTU 22.04"
#     aggregate    = "utah.cloudlab.us"
# }

# resource "cloudlab_simple_experiment" "experiment5"{
#     name = "utahexperiment2"
#     routable_ip = true
#     image        = "UBUNTU 22.04"
#     aggregate    = "utah.cloudlab.us"
# }

# resource "cloudlab_simple_experiment" "experiment6"{
#     name = "utahexperiment3"
#     routable_ip = true
#     image        = "UBUNTU 24.04"
#     aggregate    = "utah.cloudlab.us"
# }