"""Quick check of existing infrastructure for memOS.MCP"""
import asyncio
import sys

async def check_existing_services():
    print("=" * 70)
    print("Checking Existing Infrastructure for memOS.MCP")
    print("=" * 70)
    print()
    
    # Check Ollama
    print("🤖 Ollama (Embeddings)")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get('http://localhost:11434/api/tags', timeout=3)
            print(f"   Status: ✅ Running on port 11434")
            data = resp.json()
            models = [m.get('name', '') for m in data.get('models', [])]
            has_bge = any('bge-m3' in m for m in models)
            if has_bge:
                print(f"   Models: ✅ bge-m3 available ({len(models)} total)")
            else:
                print(f"   Models: ⚠️  bge-m3 NOT found ({len(models)} models)")
                print(f"   Action: Run 'ollama pull bge-m3'")
    except Exception as e:
        print(f"   Status: ❌ {e}")
    print()
    
    # Check PostgreSQL
    print("🗄️  PostgreSQL (Persistent Storage)")
    try:
        import asyncpg
        from memos_mcp.config import settings
        
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            timeout=3
        )
        print(f"   Status: ✅ Running on port 5800")
        
        # Check pgvector
        result = await conn.fetch("SELECT * FROM pg_extension WHERE extname = 'vector'")
        if result:
            print(f"   pgvector: ✅ Installed")
        else:
            print(f"   pgvector: ⚠️  NOT installed")
            print(f"   Action: CREATE EXTENSION vector;")
        
        # Check memos schema
        result = await conn.fetch(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'memos'"
        )
        if result:
            print(f"   memos schema: ✅ Initialized")
        else:
            print(f"   memos schema: ⚠️  NOT initialized")
            print(f"   Action: Run 'poetry run python scripts/init_db.py'")
        
        await conn.close()
    except Exception as e:
        print(f"   Status: ❌ {e}")
        if "password" in str(e).lower():
            print(f"   Hint: Update POSTGRES_PASSWORD in .env file")
    print()
    
    # Check Redis
    print("📦 Redis (Ephemeral Memory)")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        print(f"   Status: ✅ Running on port 6379")
    except Exception as e:
        print(f"   Status: ❌ {e}")
        print(f"   Action: docker run -d -p 6379:6379 --name memos-redis redis:7-alpine")
    print()
    
    print("=" * 70)
    print("Next Steps:")
    print("  1. Fix any ❌ or ⚠️  issues above")
    print("  2. Update .env with your PostgreSQL password")
    print("  3. Run: poetry run python -m memos_mcp --sse")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(check_existing_services())
