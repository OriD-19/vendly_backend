"""
Script to diagnose and fix database connection pool issues.
Run this to check current connections and kill stuck sessions.
"""
from app.database import engine
from sqlalchemy import text
import sys

print("\n" + "="*60)
print("DATABASE CONNECTION POOL DIAGNOSTICS")
print("="*60 + "\n")

# Check pool status
pool = engine.pool
print(f"Pool Status:")
print(f"  Pool Size: {pool.size()}")
print(f"  Checked Out: {pool.checkedout()}")
print(f"  Overflow: {pool.overflow()}")
print(f"  Checked In: {pool.checkedin()}")
print(f"\n  Total Connections: {pool.size() + pool.overflow()}")

# Check if we can get a connection
try:
    with engine.connect() as conn:
        print(f"\n✓ Can acquire new connection from pool")
        
        # Get active connections from database
        result = conn.execute(text("""
            SELECT 
                pid,
                usename,
                application_name,
                client_addr,
                state,
                query_start,
                state_change,
                query
            FROM pg_stat_activity
            WHERE datname = current_database()
                AND pid != pg_backend_pid()
            ORDER BY query_start DESC
        """))
        
        connections = result.fetchall()
        
        print(f"\n" + "="*60)
        print(f"ACTIVE DATABASE CONNECTIONS: {len(connections)}")
        print("="*60)
        
        if not connections:
            print("\nNo other active connections found.")
        else:
            for i, row in enumerate(connections, 1):
                pid, user, app, client, state, query_start, state_change, query = row
                print(f"\n#{i} PID: {pid}")
                print(f"   User: {user}")
                print(f"   App: {app}")
                print(f"   Client: {client}")
                print(f"   State: {state}")
                print(f"   Started: {query_start}")
                print(f"   Last Change: {state_change}")
                if query:
                    query_preview = query[:100].replace('\n', ' ')
                    print(f"   Query: {query_preview}...")
        
        # Check for idle connections
        idle_result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
                AND state = 'idle'
                AND pid != pg_backend_pid()
        """))
        idle_count = idle_result.scalar()
        
        print(f"\n" + "="*60)
        print(f"IDLE CONNECTIONS: {idle_count}")
        print("="*60)
        
        if idle_count > 0:
            print(f"\nWARNING: {idle_count} idle connections detected!")
            print("These may be from WebSocket connections that didn't close properly.")
            
            # Ask if user wants to kill idle connections
            if len(sys.argv) > 1 and sys.argv[1] == '--kill-idle':
                print("\nKilling idle connections...")
                kill_result = conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                        AND state = 'idle'
                        AND pid != pg_backend_pid()
                """))
                killed = sum(1 for row in kill_result if row[0])
                print(f"✓ Killed {killed} idle connections")
            else:
                print("\nTo kill idle connections, run:")
                print("  python fix_db_connections.py --kill-idle")
        
        # Check connection limits
        limit_result = conn.execute(text("""
            SELECT 
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn,
                (SELECT COUNT(*) FROM pg_stat_activity) as current_conn
        """))
        max_conn, current_conn = limit_result.fetchone()
        
        print(f"\n" + "="*60)
        print(f"CONNECTION LIMITS")
        print("="*60)
        print(f"  Max Connections: {max_conn}")
        print(f"  Current Connections: {current_conn}")
        print(f"  Available: {max_conn - current_conn}")
        print(f"  Usage: {(current_conn/max_conn)*100:.1f}%")
        
        if current_conn > max_conn * 0.8:
            print(f"\n⚠️  WARNING: Using {(current_conn/max_conn)*100:.1f}% of available connections!")
            print("   Consider:")
            print("   1. Restarting your application server")
            print("   2. Using NullPool instead of connection pooling")
            print("   3. Reducing pool_size and max_overflow in database.py")

except Exception as e:
    print(f"\n✗ Error connecting to database: {e}")
    print("\nThis usually means:")
    print("  1. Database connection pool is exhausted")
    print("  2. Database server is overloaded")
    print("  3. Network issues")
    
    print("\nIMMEDIATE FIX:")
    print("  1. Restart your application server to close all connections")
    print("  2. Run this script again to verify connections are freed")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)
print("""
For WebSocket applications with Supabase:

1. ✓ DONE: Updated WebSocket endpoint to use per-operation sessions
2. ✓ DONE: Reduced pool_size to 5 and max_overflow to 10
3. TODO: Restart your application server to apply changes
4. TODO: Monitor connection usage after deploying

If issues persist:
- Uncomment the NullPool line in database.py
- This disables connection pooling (slower but prevents leaks)
""")

print("="*60 + "\n")
