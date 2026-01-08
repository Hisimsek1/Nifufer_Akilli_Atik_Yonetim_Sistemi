import sqlite3

conn = sqlite3.connect('nilufer_waste.db')

updates = [
    ("12345678901", "Ahmet Yılmaz"),
    ("12345678902", "Ayşe Demir"),
    ("12345678903", "Mehmet Kaya"),
    ("11111111111", "Admin User")
]

for tc, name in updates:
    conn.execute("UPDATE users SET tc_number = ? WHERE name = ?", (tc, name))

conn.commit()
print("✓ Test kullanıcılarına TC numaraları eklendi")
print("\nTest Giriş Bilgileri:")
print("-" * 40)
for tc, name in updates:
    print(f"{name}: TC {tc}, Şifre: test123")

conn.close()
