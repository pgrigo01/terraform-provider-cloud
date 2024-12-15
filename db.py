# import firebase_admin
# from firebase_admin import credentials, firestore

# # Initialize Firestore
# #this file is retrieved from settings in firebase after creating a project
# cred = credentials.Certificate('serviceAccountKey.json')  # Update with the actual path to the key
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# class Vlan:
#     def __init__(self, name, experiment, ready):
#         self.name = name
#         self.experiment = experiment
#         self.ready = ready

#     def __str__(self):
#         return f'{self.name}, {self.experiment}, {self.ready}'

#     def save(self):
#         """Save or update the VLAN in Firestore."""
#         vlan_ref = db.collection('vlans').document(self.name)
#         vlan_ref.set({
#             'name': self.name,
#             'experiment': self.experiment,
#             'ready': self.ready
#         })

#     def delete(self):
#         """Delete the VLAN from Firestore."""
#         vlan_ref = db.collection('vlans').document(self.name)
#         vlan_ref.delete()

#     def updateFromCloudlabAndDB(self, app, server, proj):
#         """
#         Update VLAN readiness status from CloudLab and Firestore.

#         Args:
#         - app: Flask app for logging.
#         - server: CloudLab XML-RPC server instance.
#         - proj: Project name in CloudLab.

#         Returns:
#         - Updated Vlan instance or None if update fails.
#         """
#         app.logger.info(f"Updating VLAN {self.name} readiness from CloudLab.")
#         try:
#             # Query CloudLab API for VLAN readiness
#             params = {"proj": proj, "vlan_name": self.name}
#             exitval, response = server.checkVlanReadiness(params).apply()
            
#             if exitval == 0 and response.get("ready", False):
#                 # Update readiness in Firestore
#                 self.ready = True
#                 self.save()
#                 app.logger.info(f"VLAN {self.name} is now ready.")
#             else:
#                 app.logger.info(f"VLAN {self.name} is not ready. Response: {response}")
#             return self
#         except Exception as e:
#             app.logger.error(f"Error updating VLAN readiness: {e}")
#             return None

#     @staticmethod
#     def all():
#         """Retrieve all VLANs from Firestore."""
#         vlans = db.collection('vlans').stream()
#         return [Vlan(doc.id, doc.to_dict()['experiment'], doc.to_dict()['ready']) for doc in vlans]

#     @staticmethod
#     def filterByName(name):
#         """Retrieve a VLAN by its name."""
#         vlan_ref = db.collection('vlans').document(name)
#         doc = vlan_ref.get()
#         if doc.exists:
#             data = doc.to_dict()
#             return Vlan(name, data['experiment'], data['ready'])
#         return None
 
#     @staticmethod
#     def filterByExperiment(experiment):
#         """Retrieve VLANs by their experiment."""
#         vlans = db.collection('vlans').where('experiment', '==', experiment).stream()
#         return [Vlan(doc.id, doc.to_dict()['experiment'], doc.to_dict()['ready']) for doc in vlans]


import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firestore
cred = credentials.Certificate('serviceAccountKey.json')  # Update with the actual path to the key
firebase_admin.initialize_app(cred)
db = firestore.client()

class Vlan:
    def __init__(self, name, experiment, ready):
        self.name = name
        self.experiment = experiment
        self.ready = ready  # Ensure consistency in type (int or bool)

    def __str__(self):
        return f'{self.name}, {self.experiment}, {self.ready}'

    def save(self):
        """Save or update the VLAN in Firestore."""
        try:
            vlan_ref = db.collection('vlans').document(self.name)
            vlan_ref.set({
                'experiment': self.experiment,
                'ready': self.ready
            })
            print(f"VLAN {self.name} saved successfully.")
        except Exception as e:
            print(f"Error saving VLAN {self.name}: {e}")
            raise

    def delete(self):
        """Delete the VLAN from Firestore."""
        try:
            vlan_ref = db.collection('vlans').document(self.name)
            vlan_ref.delete()
            print(f"VLAN {self.name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting VLAN {self.name}: {e}")
            raise

    def updateFromCloudlabAndDB(self, app, server, proj):
        """
        Update VLAN readiness status from CloudLab and Firestore.

        Args:
        - app: Flask app for logging.
        - server: CloudLab XML-RPC server instance.
        - proj: Project name in CloudLab.

        Returns:
        - Updated Vlan instance or None if update fails.
        """
        app.logger.info(f"Updating VLAN {self.name} readiness from CloudLab.")
        try:
            # Query CloudLab API for VLAN readiness
            params = {"proj": proj, "vlan_name": self.name}
            exitval, response = server.checkVlanReadiness(params).apply()
            
            if exitval == 0 and response.get("ready", False):
                # Update readiness in Firestore
                self.ready = 1  # or True if using Boolean
                self.save()
                app.logger.info(f"VLAN {self.name} is now ready.")
            else:
                app.logger.info(f"VLAN {self.name} is not ready. Response: {response}")
            return self
        except Exception as e:
            app.logger.error(f"Error updating VLAN readiness: {e}")
            return None

    @staticmethod
    def all():
        """Retrieve all VLANs from Firestore."""
        try:
            vlans = db.collection('vlans').stream()
            return [Vlan(doc.id, doc.to_dict()['experiment'], doc.to_dict()['ready']) for doc in vlans]
        except Exception as e:
            print(f"Error retrieving VLANs: {e}")
            return []

    @staticmethod
    def filterByName(name):
        """Retrieve a VLAN by its name."""
        try:
            vlan_ref = db.collection('vlans').document(name)
            doc = vlan_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return Vlan(name, data['experiment'], data['ready'])
            return None
        except Exception as e:
            print(f"Error filtering VLAN by name {name}: {e}")
            return None

    @staticmethod
    def filterByExperiment(experiment):
        """Retrieve VLANs by their experiment."""
        try:
            vlans = db.collection('vlans').where('experiment', '==', experiment).stream()
            return [Vlan(doc.id, doc.to_dict()['experiment'], doc.to_dict()['ready']) for doc in vlans]
        except Exception as e:
            print(f"Error filtering VLANs by experiment {experiment}: {e}")
            return []
