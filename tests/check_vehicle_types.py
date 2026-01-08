import sqlite3

conn = sqlite3.connect('nilufer_waste.db')
cursor = conn.cursor()

print('vehicle_types table structure:')
cursor.execute('PRAGMA table_info(vehicle_types)')
cols = cursor.fetchall()
for c in cols:
    print(f'  {c[1]} ({c[2]})')

print('\nSample data:')
cursor.execute('SELECT * FROM vehicle_types LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()
