import sqlite3

from CloudLabAPI.src.emulab_sslxmlrpc.client import api

database_file = 'database.db'


def get_db_connection():
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row
    return conn


connection = get_db_connection()

with open('schema.sql') as f:
    connection.executescript(f.read())

connection.close()


class Vlan:
    def __init__(self, name, experiment, ready):
        self.name = name
        self.experiment = experiment
        self.ready = ready

    def __str__(self):
        return f'{self.name}, {self.experiment}, {self.ready}'

    def save(self):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO vlan (name, experiment, ready) VALUES (?, ?, ?)",
            (self.name, self.experiment, self.ready))
        connection.commit()
        connection.close()

    def delete(self):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute("DELETE FROM vlan WHERE name=?", (self.name,))
        connection.commit()
        connection.close()

    def updateFromCloudlabAndDB(self, app, server, project):
        params = {
            "experiment": f"{project},{self.experiment}"
        }
        (exitval, response) = api.experimentStatus(server, params).apply()
        app.logger.debug(exitval)
        app.logger.debug(response)
        if exitval == 0 and response.output.split()[1] != 'failed':
            self.ready = response.output.split()[1] not in ['provisioning', 'failed', 'terminating', 'terminated',
                                                            'canceled']
            self.save()
        else:
            self.delete()
        return Vlan.filterByName(name=self.name)

    @staticmethod
    def all():
        conn = get_db_connection()
        vlans = conn.execute('SELECT * FROM vlan').fetchall()
        vlans_list = []
        for vlan in vlans:
            vlans_list.append(Vlan(vlan['name'], vlan['experiment'], vlan['ready']))
        conn.close()
        return vlans_list

    @staticmethod
    def filterByName(name):
        conn = get_db_connection()
        vlan = conn.execute(f'SELECT * FROM vlan WHERE name="{name}"').fetchone()
        conn.close()
        if vlan is None:
            return None
        return Vlan(vlan['name'], vlan['experiment'], vlan['ready'])

    @staticmethod
    def filterByExperiment(experiment):
        conn = get_db_connection()
        vlan = conn.execute(f'SELECT * FROM vlan WHERE experiment="{experiment}"').fetchone()
        conn.close()
        if vlan is None:
            return None
        return Vlan(vlan['name'], vlan['experiment'], vlan['ready'])
