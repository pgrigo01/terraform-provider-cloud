#!/usr/bin/env python3
import sqlite3

def main():
    # Connect to the SQLite database file
    conn = sqlite3.connect('experiments.db')
    cursor = conn.cursor()
    
    # Query all experiment records
    cursor.execute("SELECT name, uuid, project, status, created_at, expireAt FROM experiments")
    rows = cursor.fetchall()
    
    if not rows:
        print("No experiments found in the database.")
    else:
        for row in rows:
            print("Experiment:")
            print(f"  Name       : {row[0]}")
            print(f"  UUID       : {row[1]}")
            print(f"  Project    : {row[2]}")
            print(f"  Status     : {row[3]}")
            print(f"  Created At : {row[4]}")
            print(f"  Expire At  : {row[5]}")
            print("-" * 40)
    
    # Close the connection
    conn.close()

if __name__ == '__main__':
    main()
