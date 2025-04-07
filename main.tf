
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

# # # # Openstack experiment with 1 node in a specific cluster (winsconstin) and a specific node type (c220g1)

# resource "cloudlab_openstack_experiment" "experiment1" {
#   name               = "experiment1"
#   release            = "zed" # zed is the most recent in this profile: ubuntu 22.04 you can visit the profile to see available releases https://www.cloudlab.us/show-profile.php?uuid=f661a302-e5a7-11e7-b179-90e2ba22fee4 `
#   compute_node_count = 0
#   os_node_type       = ""   # default:"" is emulab. see node-type.txt for more or visit https://www.cloudlab.us/resinfo.php to see available node types 
#   ml2plugin          = "openvswitch"
#   extra_image_urls   = ""
# }


# # # # Openstack experiment with 1 node specifically c220g5 which is in winsconstin cluster.

# resource "cloudlab_openstack_experiment" "experiment2" {
#   name               = "experiment2"
#   release            = "zed" 
#   compute_node_count = 0
#   os_node_type       = ""   # default:"" is Any available node. see node-type.txt for more or visit https://www.cloudlab.us/resinfo.php to see available node types 
#   ml2plugin          = "openvswitch"
#   extra_image_urls   = ""
# }


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
#   extra_disk_space = 300 # added option to ask for a 300GB local file system mounted at /mydata --> see with command: df -h only accessible within the experiment
#   node_count = 3 #nodes that are on the same experiment
# }


# # # # This cloudlab_simple_experiment resource creates 1 node on an experiment without a node-local-dataset and is allocated in utah.cloudlab.us cluster

# resource "cloudlab_simple_experiment" "uthaexperiment1" {
#   name         = "uthaexperiment1"
#   routable_ip  = true
#   image        = "UBUNTU 22.04"
#   aggregate    = "utah.cloudlab.us"
#   node_count = 1
# }

# # # This cloudlab_simple_experiment resource creates 1 node on an experiment without a node-local-dataset and is allocated in wisc.cloudlab.us cluster

# resource "cloudlab_simple_experiment" "wiscexperiment1" {
#   name         = "wiscexperiment1"
#   routable_ip  = true
#   image        = "UBUNTU 24.04"
#   aggregate    = "wisc.cloudlab.us"
# }

