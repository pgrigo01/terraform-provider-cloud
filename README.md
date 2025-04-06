<!-- markdownlint-disable first-line-h1 no-inline-html -->
<a href="https://terraform.io">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/terraform_logo_dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/terraform_logo_light.svg">
    <img src=".github/terraform_logo_light.svg" alt="Terraform logo" title="Terraform" align="right" height="50">
  </picture>
</a>

# Terraform CloudLab Provider
[discuss-badge]: https://img.shields.io/badge/discuss-terraform--cloudlab-623CE4.svg?style=flat
![Forums][discuss-badge]

The [CloudLab Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) allows [Terraform](https://terraform.io) to manage [CloudLab](https://www.cloudlab.us/) resources.

## Usage Example
```
#When changing versions run:
# terraform init -upgrade 

#If first time run : terraform init 
#If you want to see the changes in the plan  run: terraform plan 
#If you want to apply the plan run: terraform apply 

# RESOURCE BLOCKS EXPLAINED
# cloudlab_openstack_experiment have openstack storage options and also have a shared file system between experiments 
# on the same cluster,which is persistent too for example on emulab it is under /proj/UCY-CS499-DC/ 100GB of shared storage
#  USE: df -h on node to find the 100GB of shared storage under /proj/ directory in all clusters, anything you add there will remain.

# cloudlab_simple_experiment has the option to create a node-local-dataset which is not persistent and will be deleted when the node is terminated this is
# called extra-disk-space is essentialy a Node-Local-Dataset.
# A Node-Local-Dataset is stored on the local disk of the node and will be deleted when the node is terminated.(not persistent).This is
# useful if you know you need more storage for an experiment but you don't have to keep it later on.

# In general if you dont need a shared file system between experiments on the same cluster use cloudlab_simple_experiment since it is easiet to define.



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


# Uncomment the following Resource Blocks  and run terraform applyto see the experiments starting
# Comment back later  if you want to terminate them and run terraform apply again

# # # # Openstack experiment with 1 node in a specific cluster (winsconstin) and a specific node type (c220g1)

resource "cloudlab_openstack_experiment" "experiment1" {
  name               = "experiment1"
  release            = "zed" # zed is the most recent in this profile: ubuntu 22.04 you can visit the profile to see available releases https://www.cloudlab.us/show-profile.php?uuid=f661a302-e5a7-11e7-b179-90e2ba22fee4 `
  compute_node_count = 0
  os_node_type       = "c220g1"   # default:"" is emulab. see node-type.txt for more or visit https://www.cloudlab.us/resinfo.php to see available node types 
  ml2plugin          = "openvswitch"
  extra_image_urls   = ""
}


# # # Openstack experiment with 1 node specifically c220g5 which is in winsconstin cluster.

resource "cloudlab_openstack_experiment" "experiment2" {
  name               = "experiment2"
  release            = "zed" 
  compute_node_count = 0
  os_node_type       = "c220g5"   # default:"" is Any available node. see node-type.txt for more or visit https://www.cloudlab.us/resinfo.php to see available node types 
  ml2plugin          = "openvswitch"
  extra_image_urls   = ""
}


# resource "cloudlab_vlan" "my_vlan" {
#   name        = "vlan"
#   subnet_mask = "255.255.255.0"
# }


# # # This cloudlab_simple_experiment resource creates 3 nodes on an experiment that has a node-local-dataset of 50GB  and is allocated in emulab.net cluster

# resource "cloudlab_simple_experiment" "emulabexp1" {
#   name         = "emulabexp1"
#   routable_ip  = true
#   image        = "UBUNTU 24.04"
#   aggregate    = "emulab.net"
#   extra_disk_space = 300 # added option to ask for a 50GB local file system mounted at /mydata --> see with command: df -h only accessible within the experiment
#   node_count = 2 #nodes that are on the same experiment
# }

# # # # This cloudlab_simple_experiment resource creates 2 nodes on an experiment with a node-local-dataset of 50GB  and is allocated in emulab.net cluster

# resource "cloudlab_simple_experiment" "uthaexperiment1" {
#   name         = "uthaexperiment1"
#   routable_ip  = true
#   image        = "UBUNTU 22.04"
#   aggregate    = "utah.cloudlab.us"
#   node_count = 1
# }

# # # # This cloudlab_simple_experiment resource creates 1 node on an experiment without a node-local-dataset and is allocated in wisc.cloudlab.us cluster

# resource "cloudlab_simple_experiment" "wiscexperiment1" {
#   name         = "wiscexperiment1"
#   routable_ip  = true
#   image        = "UBUNTU 24.04"
#   aggregate    = "wisc.cloudlab.us"
# }

```
