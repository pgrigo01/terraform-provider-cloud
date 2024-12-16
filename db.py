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
            print(f"VLAN '{self.name}' saved successfully.")
        except Exception as e:
            print(f"Error saving VLAN '{self.name}': {e}")
            raise

    def delete(self):
        """Delete the VLAN from Firestore."""
        try:
            vlan_ref = db.collection('vlans').document(self.name)
            vlan_ref.delete()
            print(f"VLAN '{self.name}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting VLAN '{self.name}': {e}")
            raise

    def update_from_cloudlab_and_db(self, app, server, proj):
        """
        Update VLAN readiness status from CloudLab and Firestore.

        Args:
        - app: Flask app for logging.
        - server: CloudLab XML-RPC server instance.
        - proj: Project name in CloudLab.

        Returns:
        - Updated Vlan instance or None if update fails.
        """
        app.logger.info(f"Updating VLAN '{self.name}' readiness from CloudLab.")
        try:
            # Query CloudLab API for VLAN readiness
            params = {"proj": proj, "vlan_name": self.name}
            exitval, response = server.checkVlanReadiness(params).apply()

            if exitval == 0 and response.get("ready", False):
                # Update readiness in Firestore
                self.ready = 1  # or True if using Boolean
                self.save()
                app.logger.info(f"VLAN '{self.name}' is now ready.")
            else:
                app.logger.info(f"VLAN '{self.name}' is not ready. Response: {response}")
            return self
        except Exception as e:
            app.logger.error(f"Error updating VLAN readiness: {e}")
            return None

    @staticmethod
    def all():
        """Retrieve all VLANs from Firestore."""
        try:
            vlans = db.collection('vlans').stream()
            return [Vlan(doc.id, doc.to_dict().get('experiment', ''), doc.to_dict().get('ready', 0)) for doc in vlans]
        except Exception as e:
            print(f"Error retrieving VLANs: {e}")
            return []

    @staticmethod
    def filter_by_name(name):
        """Retrieve a VLAN by its name."""
        try:
            vlan_ref = db.collection('vlans').document(name)
            doc = vlan_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return Vlan(name, data.get('experiment', ''), data.get('ready', 0))
            print(f"VLAN '{name}' does not exist.")
            return None
        except Exception as e:
            print(f"Error filtering VLAN by name '{name}': {e}")
            return None

    @staticmethod
    def filter_by_experiment(experiment):
        """Retrieve VLANs by their experiment."""
        try:
            vlans = db.collection('vlans').where('experiment', '==', experiment).stream()
            return [Vlan(doc.id, doc.to_dict().get('experiment', ''), doc.to_dict().get('ready', 0)) for doc in vlans]
        except Exception as e:
            print(f"Error filtering VLANs by experiment '{experiment}': {e}")
            return []

class Profile:
    def __init__(self, profile_id, name, project):
        self.profile_id = profile_id
        self.name = name
        self.project = project

    def save(self):
        """Save or update the Profile in Firestore."""
        try:
            profile_ref = db.collection('profiles').document(self.profile_id)
            profile_ref.set({
                'name': self.name,
                'project': self.project
            })
            print(f"Profile '{self.profile_id}' saved successfully.")
        except Exception as e:
            print(f"Error saving Profile '{self.profile_id}': {e}")
            raise

    @staticmethod
    def get_or_create(profile_id, default_name="Default Profile", default_project="Default Project"):
        """Retrieve a Profile by ID or create it if it doesn't exist."""
        try:
            profile_ref = db.collection('profiles').document(profile_id)
            doc = profile_ref.get()
            if doc.exists:
                print(f"Profile '{profile_id}' found.")
                data = doc.to_dict()
                return Profile(profile_id, data.get('name', default_name), data.get('project', default_project))
            else:
                print(f"Profile '{profile_id}' does not exist. Creating it.")
                new_profile = Profile(profile_id, default_name, default_project)
                new_profile.save()
                return new_profile
        except Exception as e:
            print(f"Error retrieving or creating Profile '{profile_id}': {e}")
            raise
