import sqlite3

conn = sqlite3.connect('nilufer_waste.db')
cursor = conn.cursor()

# Tabloları listele
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])

# Vehicles tablosu varsa yapısını göster
if ('vehicles',) in tables:
    cursor.execute('PRAGMA table_info(vehicles)')
    print('\nVehicles columns:', [(c[1], c[2]) for c in cursor.fetchall()])
    
    cursor.execute('SELECT * FROM vehicles LIMIT 3')
    print('\nSample vehicles:', cursor.fetchall())

# Containers bilgisi
cursor.execute('SELECT COUNT(*) FROM containers')
print(f'\nTotal containers: {cursor.fetchone()[0]}')

cursor.execute('SELECT latitude, longitude FROM containers WHERE latitude IS NOT NULL LIMIT 3')
print('Sample container locations:', cursor.fetchall())

conn.close()
