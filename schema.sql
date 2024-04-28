DROP TABLE IF EXISTS vlan;

CREATE TABLE vlan (
    name varchar PRIMARY KEY,
    experiment VARCHAR NOT NULL,
    ready INT(1) NOT NULL
);