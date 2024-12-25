from flask import Flask, request, jsonify
from db import Vlan
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/vlans', methods=['POST'])
def create_vlan():
    data = request.json
    if 'name' not in data or 'experiment' not in data:
        return jsonify({'error': 'Missing name or experiment'}), 400
    
    vlan = Vlan(data['name'], data['experiment'], data.get('ready', False))
    vlan.save()
    return jsonify({'message': f"VLAN '{vlan.name}' created successfully."}), 201

@app.route('/vlans/<vlan_name>', methods=['GET'])
def get_vlan(vlan_name):
    vlan = Vlan.filterByName(vlan_name)
    if vlan:
        return jsonify({
            'name': vlan.name,
            'experiment': vlan.experiment,
            'ready': vlan.ready
        }), 200
    return jsonify({'error': 'VLAN not found'}), 404

@app.route('/vlans', methods=['GET'])
def list_vlans():
    vlans = Vlan.all()
    vlans_data = [{'name': v.name, 'experiment': v.experiment, 'ready': v.ready} for v in vlans]
    return jsonify(vlans_data), 200

@app.route('/vlans/<vlan_name>', methods=['DELETE'])
def delete_vlan(vlan_name):
    vlan = Vlan.filterByName(vlan_name)
    if vlan:
        vlan.delete()
        return jsonify({'message': f"VLAN '{vlan_name}' deleted."}), 200
    return jsonify({'error': 'VLAN not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=8080)
