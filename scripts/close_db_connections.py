#!/usr/bin/env python3
"""
Emergency script to close all idle database connections.
Run this before deployment if you're hitting connection limits.

Usage:
    python scripts/close_db_connections.py
    python scripts/close_db_connections.py --force  # Kill all app connections
"""
import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def close_idle_connections(force=False):
    """Close idle database connections"""
    print("\n" + "="*70)
    print("EMERGENCY DATABASE CONNECTION CLEANUP")
    print("="*70 + "\n")
    
    # Create a direct connection (not using pooling)
    engine = create_engine(Config.DATABASE_URL, poolclass=None)
    
    try:
        with engine.connect() as conn:
            # Get current connection stats
            print("📊 Current connection status:\n")
            result = conn.execute(text("""
                SELECT 
                    state,
                    COUNT(*) as count,
                    application_name
                FROM pg_stat_activity
                WHERE datname = current_database()
                    AND pid != pg_backend_pid()
                GROUP BY state, application_name
                ORDER BY count DESC
            """))
            
            for row in result:
                state, count, app_name = row
                print(f"   {state:15s} {count:3d} connections  ({app_name})")
            
            # Get total
            total_result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_stat_activity
                WHERE datname = current_database()
                    AND pid != pg_backend_pid()
            """))
            total = total_result.scalar()
            print(f"\n   Total: {total} connections")
            
            # Close idle connections
            print(f"\n{'='*70}")
            if force:
                print("⚠️  FORCE MODE: Closing ALL application connections")
                print("="*70 + "\n")
                
                result = conn.execute(text("""
                    SELECT 
                        pg_terminate_backend(pid),
                        pid,
                        usename,
                        application_name,
                        state
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                        AND pid != pg_backend_pid()
                        AND usename NOT LIKE 'supabase%'
                        AND usename NOT LIKE 'postgres%'
                """))
                
                killed = 0
                for row in result:
                    terminated, pid, user, app, state = row
                    if terminated:
                        killed += 1
                        print(f"   ✓ Killed PID {pid}: {user}/{app} ({state})")
                
                print(f"\n✅ Force-closed {killed} connections")
            else:
                print("🧹 Closing IDLE connections only")
                print("="*70 + "\n")
                
                result = conn.execute(text("""
                    SELECT 
                        pg_terminate_backend(pid),
                        pid,
                        usename,
                        application_name,
                        state_change
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                        AND state = 'idle'
                        AND pid != pg_backend_pid()
                        AND usename NOT LIKE 'supabase%'
                        AND usename NOT LIKE 'postgres%'
                        AND state_change < NOW() - INTERVAL '5 minutes'
                """))
                
                killed = 0
                for row in result:
                    terminated, pid, user, app, state_change = row
                    if terminated:
                        killed += 1
                        print(f"   ✓ Killed PID {pid}: {user}/{app} (idle since {state_change})")
                
                print(f"\n✅ Closed {killed} idle connections")
                
                if killed == 0:
                    print("   No idle connections found (or they are recent)")
                    print("\n   💡 Tip: Use --force to close all app connections")
            
            # Show updated stats
            print(f"\n{'='*70}")
            print("📊 Updated connection status:")
            print("="*70 + "\n")
            
            updated_result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_stat_activity
                WHERE datname = current_database()
                    AND pid != pg_backend_pid()
            """))
            updated_total = updated_result.scalar()
            print(f"   Remaining connections: {updated_total}")
            print(f"   Freed: {total - updated_total}")
            
            # Get connection limit
            limit_result = conn.execute(text("""
                SELECT setting::int 
                FROM pg_settings 
                WHERE name = 'max_connections'
            """))
            max_conn = limit_result.scalar()
            
            print(f"\n   Max allowed: {max_conn}")
            print(f"   Available: {max_conn - updated_total}")
            print(f"   Usage: {(updated_total/max_conn)*100:.1f}%")
            
            if updated_total < max_conn * 0.5:
                print(f"\n✅ Good! Connection usage is healthy")
            elif updated_total < max_conn * 0.8:
                print(f"\n⚠️  Warning: Connection usage is getting high")
            else:
                print(f"\n🚨 CRITICAL: Connection usage is very high!")
                print("   Consider restarting your application")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your DATABASE_URL is configured correctly")
        return 1
    
    finally:
        engine.dispose()
    
    print(f"\n{'='*70}\n")
    return 0

if __name__ == "__main__":
    force = "--force" in sys.argv
    
    if force:
        confirm = input("\n⚠️  Are you sure you want to force-close ALL connections? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    sys.exit(close_idle_connections(force))
