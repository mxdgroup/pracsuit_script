# How to Find Your Railway TCP Proxy Port

## The Problem
Railway PostgreSQL requires a **TCP Proxy Port** for external connections, which is **NOT** the standard PostgreSQL port 5432.

## Quick Steps to Find Your Port

### Method 1: Railway Dashboard (Easiest)

1. Go to [Railway Dashboard](https://railway.app/)
2. Select your project
3. Click on your **PostgreSQL** service
4. Click on the **"Variables"** tab
5. Look for: `RAILWAY_TCP_PROXY_PORT`
   - This will be a number like `12345`, `45678`, etc.
6. Copy that number

### Method 2: Connection String

1. In the same Variables tab, find: `DATABASE_PUBLIC_URL`
2. It will look like:
   ```
   postgresql://postgres:password@switchyard.proxy.rlwy.net:XXXXX/railway
   ```
3. The `XXXXX` after `switchyard.proxy.rlwy.net:` is your TCP proxy port

### Method 3: Connect Tab

1. Click on the **"Connect"** tab in your PostgreSQL service
2. Look for the **"Public Networking"** section
3. Find the port number listed there

## Update Your .env File

Once you have the port number (let's say it's `12345`), update your `.env`:

```env
POSTGRES_HOST=switchyard.proxy.rlwy.net
POSTGRES_PORT=12345  # <-- Replace with your actual port
POSTGRES_USER=postgres
POSTGRES_PASSWORD=qktaqSHIazfnIgTwdVmWoJWRHvFxtPVS
POSTGRES_ADMIN_DB=railway
```

## Test Your Connection

After updating the port, run:

```bash
python test_db_setup.py
```

You should see:
```
Testing PostgreSQL connection...
Host: switchyard.proxy.rlwy.net
Port: 12345
User: postgres
Database: railway
[SUCCESS] Successfully connected to PostgreSQL!
```

## Common Port Numbers

Railway typically assigns ports in these ranges:
- 10000-65535 (random assignment)
- Usually 5-digit numbers like: 12345, 23456, 34567

## Still Not Working?

### Check Firewall
Make sure your firewall allows outbound connections to Railway:
- Host: `switchyard.proxy.rlwy.net`
- Port: Your TCP proxy port

### Check Railway Service Status
1. Go to your Railway dashboard
2. Verify the PostgreSQL service is **running** (green indicator)
3. Check for any error messages

### Try SSL Connection
Some Railway instances require SSL. Update your code to include:

```python
conn = psycopg2.connect(
    host='switchyard.proxy.rlwy.net',
    port='YOUR_PORT',
    user='postgres',
    password='qktaqSHIazfnIgTwdVmWoJWRHvFxtPVS',
    database='railway',
    sslmode='require'  # Add this
)
```

## Alternative: Use DATABASE_PUBLIC_URL

Instead of individual parameters, you can use the full connection string:

In your `.env`:
```env
DATABASE_URL=postgresql://postgres:qktaqSHIazfnIgTwdVmWoJWRHvFxtPVS@switchyard.proxy.rlwy.net:XXXXX/railway
```

Then in your Python code:
```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
```

This is often simpler and less error-prone!

