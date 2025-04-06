resource "cloudlab_vm" "my-cloudlab-vm" {
  name         = "vm-name"
  project      = "project-name"
  profile_uuid = "profile-uuid"
  vlan         = []
}