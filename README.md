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

provider "cloudlab" {
  credentials_path = "./credentials-decrypted.pem"
}

resource "cloudlab_vlan" "my-cloudlab-vlan" {
  name        = "vlan-name"
  subnet_mask = "255.255.255.0"
}

resource "cloudlab_vm" "my-cloudlab-vm" {
  name         = "vm-name"
  project      = "project-name"
  profile_uuid = "profile-uuid"
  vlan         = []
}
```
