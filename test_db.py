from db import Vlan

if __name__ == '__main__':
    # Create and save a VLAN
    vlan1 = Vlan('vlan1', 'experiment1', True)
    vlan1.save()
    print("Saved VLAN:", vlan1)

    # Fetch all VLANs
    print("All VLANs:")
    for vlan in Vlan.all():
        print(vlan)

    # Fetch a VLAN by name
    vlan_by_name = Vlan.filterByName('vlan1')
    print("VLAN by Name:", vlan_by_name)

    #Delete a VLAN
    vlan1.delete()
    print("Deleted VLAN:", vlan1)
