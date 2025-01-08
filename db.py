# db.py
import firebase_admin
from firebase_admin import credentials, firestore
import logging as std_logging
from CloudLabAPI.src.emulab_sslxmlrpc.client import api

# Configure Logging
std_logging.basicConfig(level=std_logging.INFO)
logger = std_logging.getLogger(__name__)

# Initialize Firebase App only if not already initialized
def initialize_firebase():
    try:
        # Attempt to get the default app
        firebase_admin.get_app()
        logger.info("Firebase app already initialized.")
    except ValueError:
        try:
            # Path to your service account key
            cred = credentials.Certificate('serviceAccountKey.json')  # Update this path or include the file in this directory
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise e

# Initialize Firestore client
initialize_firebase()
db = firestore.client()

# class Vlan:
#     COLLECTION_NAME = 'vlans'

#     def __init__(self, name, experiment, ready):
#         self.name = name
#         self.experiment = experiment
#         self.ready = ready

#     def __str__(self):
#         return f'{self.name}, {self.experiment}, {self.ready}'

#     def save(self):
#         logger.info(f"Saving VLAN '{self.name}' for experiment '{self.experiment}'.")
#         try:
#             vlan_data = {
#                 'name': self.name,
#                 'experiment': self.experiment,
#                 'ready': self.ready
#             }
#             db.collection(self.COLLECTION_NAME).document(self.name).set(vlan_data)
#             logger.info(f"VLAN '{self.name}' saved successfully.")
#         except Exception as e:
#             logger.error(f"Error saving VLAN '{self.name}': {e}")
#             raise e

#     def delete(self):
#         try:
#             db.collection(self.COLLECTION_NAME).document(self.name).delete()
#             logger.info(f"VLAN '{self.name}' deleted from Firestore.")
#         except Exception as e:
#             logger.error(f"Error deleting VLAN '{self.name}': {e}")
#             raise e

#     @staticmethod
#     def all():
#         try:
#             vlans_ref = db.collection(Vlan.COLLECTION_NAME)
#             vlans = vlans_ref.stream()
#             vlans_list = [
#                 Vlan(vlan.to_dict()['name'], vlan.to_dict()['experiment'], vlan.to_dict()['ready'])
#                 for vlan in vlans
#             ]
#             logger.info("Retrieved all VLANs from Firestore.")
#             return vlans_list
#         except Exception as e:
#             logger.error(f"Error retrieving all VLANs: {e}")
#             return []

#     @staticmethod
#     def filterByName(name):
#         try:
#             vlan_ref = db.collection(Vlan.COLLECTION_NAME).document(name).get()
#             if vlan_ref.exists:
#                 vlan_data = vlan_ref.to_dict()
#                 logger.info(f"VLAN '{name}' retrieved from Firestore.")
#                 return Vlan(vlan_data['name'], vlan_data['experiment'], vlan_data['ready'])
#             logger.warning(f"VLAN '{name}' does not exist in Firestore.")
#             return None
#         except Exception as e:
#             logger.error(f"Error filtering VLAN by name '{name}': {e}")
#             return None

#     @staticmethod
#     def filterByExperiment(experiment):
#         try:
#             vlans_ref = db.collection(Vlan.COLLECTION_NAME)
#             query = vlans_ref.where('experiment', '==', experiment).stream()
#             vlans = [
#                 Vlan(vlan.to_dict()['name'], vlan.to_dict()['experiment'], vlan.to_dict()['ready'])
#                 for vlan in query
#             ]
#             if vlans:
#                 logger.info(f"VLANs for experiment '{experiment}' retrieved from Firestore.")
#                 return vlans[0]  
#             logger.warning(f"No VLANs found for experiment '{experiment}' in Firestore.")
#             return None
#         except Exception as e:
#             logger.error(f"Error filtering VLAN by experiment '{experiment}': {e}")
#             return None

if __name__ == "__main__":
    logger.info("db.py executed as a script.")
    

