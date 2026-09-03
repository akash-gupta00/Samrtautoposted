import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Database connect karo
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Akashpqs",
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Pehle saare connections terminate karo
    print("🔴 Terminating all connections to smartautopost_db...")
    cursor.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = 'smartautopost_db'
        AND pid <> pg_backend_pid();
    """)
    print("✅ All connections terminated")
    
    # Database drop
    cursor.execute("DROP DATABASE IF EXISTS smartautopost_db;")
    print("✅ Database dropped")
    
    # Database create
    cursor.execute("CREATE DATABASE smartautopost_db;")
    print("✅ Database created")
    
    cursor.close()
    conn.close()
    print("🎉 Database reset successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")