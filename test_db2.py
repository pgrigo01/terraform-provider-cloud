from db import Vlan

vlan1 = Vlan("test-vlan", "test-exp", True)
vlan1.save()

found_vlan = Vlan.filterByName("test-vlan")
if found_vlan:
    print(f"Found VLAN: {found_vlan.name}, Ready: {found_vlan.ready}")
