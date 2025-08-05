import sqlite3

conn = sqlite3.connect('driver.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT ul.id, ul.user_id, ul.telegram_id, ul.latitude, ul.longitude, ul.is_at_work, ul.created_at, u.role
    FROM user_locations ul
    JOIN users u ON ul.user_id = u.id
    ORDER BY ul.id DESC
''')
rows = cursor.fetchall()
print("id | user_id | telegram_id | latitude | longitude | is_at_work | created_at | role")
for row in rows:
    print(row)
conn.close() 