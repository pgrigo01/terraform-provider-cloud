resource "cloudlab_vlan" "my-cloudlab-vlan" {
  name        = "vm-name"
  subnet_mask = "255.255.255.0"
}