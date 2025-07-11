#!/usr/bin/env python3
"""
Check server health and identify any issues.
"""

import httpx
import asyncio
import json

async def check_endpoints():
    """Check various server endpoints for errors"""
    
    base_url = "http://localhost:6001"
    
    endpoints = [
        ("/health", "GET", None),
        ("/api/docs", "GET", None),
        ("/api/metrics", "GET", None),
    ]
    
    print("🔍 Checking server health...\n")
    
    async with httpx.AsyncClient() as client:
        for endpoint, method, data in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                
                if method == "GET":
                    response = await client.get(url, timeout=5)
                else:
                    response = await client.post(url, json=data, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {method} {endpoint} - OK")
                    if endpoint == "/health":
                        health_data = response.json()
                        print(f"   Status: {health_data.get('status')}")
                        services = health_data.get('services', {})
                        for service, status in services.items():
                            emoji = "✅" if status == "healthy" else "❌"
                            print(f"   {emoji} {service}: {status}")
                elif response.status_code == 404:
                    print(f"⚠️  {method} {endpoint} - Not Found")
                else:
                    print(f"❌ {method} {endpoint} - Status: {response.status_code}")
                    if response.content:
                        try:
                            error_data = response.json()
                            print(f"   Error: {error_data}")
                        except:
                            print(f"   Response: {response.text[:200]}")
                
            except httpx.TimeoutException:
                print(f"⏱️  {method} {endpoint} - Timeout")
            except httpx.ConnectError:
                print(f"🔌 {method} {endpoint} - Connection Error (Is the server running?)")
            except Exception as e:
                print(f"❌ {method} {endpoint} - Error: {type(e).__name__}: {e}")
            
            print()

async def check_database():
    """Check database connectivity"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from src.models.database import SessionLocal
        from src.models.user import User
        
        print("🗄️  Checking database...\n")
        
        db = SessionLocal()
        try:
            # Try a simple query
            user_count = db.query(User).count()
            print(f"✅ Database connection OK")
            print(f"   Total users: {user_count}")
            
            # Check for admin users
            admin_count = db.query(User).filter(
                (User.is_admin == True) | (User.is_superadmin == True)
            ).count()
            print(f"   Admin users: {admin_count}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
    
    print()

async def main():
    """Run all health checks"""
    await check_endpoints()
    await check_database()
    
    print("\n📊 Health Check Complete!")

if __name__ == "__main__":
    asyncio.run(main())