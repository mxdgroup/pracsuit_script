# PostgreSQL Database Setup Guide

## Railway Database Configuration

### Connection Details
Your Railway PostgreSQL instance is configured with:
- **Host**: `switchyard.proxy.rlwy.net`
- **Port**: Check Railway dashboard for your TCP proxy port
- **User**: `postgres`
- **Database**: `railway` (admin database)

### Required Environment Variables

Update your `.env` file with the following:

```env
POSTGRES_HOST=switchyard.proxy.rlwy.net
POSTGRES_PORT=YOUR_RAILWAY_TCP_PROXY_PORT
POSTGRES_USER=postgres
POSTGRES_PASSWORD=qktaqSHIazfnIgTwdVmWoJWRHvFxtPVS
POSTGRES_ADMIN_DB=railway
```

### Finding Your Railway TCP Proxy Port

1. Login to [Railway](https://railway.app/)
2. Navigate to your project
3. Click on your PostgreSQL service
4. Go to **Variables** or **Connect** tab
5. Look for `RAILWAY_TCP_PROXY_PORT` - it will be a number like `12345`

## How the Database System Works

### 1. Email Processing Flow

```
Email Received → Extract Clinic Name → Create Database → Create Tables
```

### 2. Clinic Name Extraction

The system extracts the clinic name from the email's "to" field:

| Email Address | Extracted Clinic | Database Name |
|---------------|------------------|---------------|
| `developers.mxd+supertest@gmail.com` | supertest | `supertest` |
| `clinic+demo-clinic@example.com` | demo-clinic | `demo_clinic` |
| `admin+test_clinic_123@test.com` | test_clinic_123 | `test_clinic_123` |

**Rules:**
- Extracts text between `+` and `@`
- Converts to lowercase
- Replaces non-alphanumeric characters with underscores
- Result becomes the database name

### 3. Table Name Extraction

Tables are created based on the attachment filename:

| Filename | Table Name |
|----------|------------|
| `Appointment Report 281025.xlsx` | `appointments` |
| `Invoice Summary.xlsx` | `invoices` |
| `Client List.xlsx` | `clients` |

**Rules:**
- Takes the first word of the filename
- Converts to lowercase
- Adds 's' if not already plural

### 4. Database Schema

Each clinic database contains:

#### Appointments Table
```sql
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    appointment_date TIMESTAMP,
    client VARCHAR(255),
    appointment_type VARCHAR(255),
    profession VARCHAR(255),
    client_duration NUMERIC,
    practitioner VARCHAR(255),
    business VARCHAR(255),
    appointment_status VARCHAR(100),
    column_number NUMERIC,
    billed_status VARCHAR(100),
    clinical_note TEXT,
    client_id BIGINT,
    appointment_id BIGINT UNIQUE,
    address_1 VARCHAR(255),
    address_2 VARCHAR(255),
    address_3 VARCHAR(255),
    address_4 VARCHAR(255),
    suburb VARCHAR(100),
    state VARCHAR(100),
    postcode VARCHAR(20),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_appointments_date` on `appointment_date`
- `idx_appointments_client_id` on `client_id`
- `idx_appointments_appointment_id` on `appointment_id`

## Testing Your Setup

### 1. Test Database Connection

```bash
python test_db_setup.py
```

This script will:
- ✓ Test connection to PostgreSQL
- ✓ Verify clinic name extraction logic
- ✓ Verify table name extraction logic
- ✓ Create a test database
- ✓ Create a test appointments table
- ✓ Clean up test resources

### 2. Manual Database Connection

You can connect manually using `psql`:

```bash
psql -h switchyard.proxy.rlwy.net -p YOUR_PORT -U postgres -d railway
```

Or using a GUI tool like:
- **pgAdmin**: [https://www.pgadmin.org/](https://www.pgadmin.org/)
- **DBeaver**: [https://dbeaver.io/](https://dbeaver.io/)
- **TablePlus**: [https://tableplus.com/](https://tableplus.com/)

### 3. Verify Database Creation

After processing an email, check if the database was created:

```sql
-- Connect to the admin database (railway)
SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1', 'railway');
```

### 4. Verify Table Creation

```sql
-- Connect to a specific clinic database
\c supertest  -- Replace 'supertest' with your clinic name

-- List all tables
\dt

-- View appointments table structure
\d appointments

-- Query appointments
SELECT * FROM appointments LIMIT 10;
```

## Common Operations

### List All Clinic Databases

```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_ADMIN_DB')
)

cursor = conn.cursor()
cursor.execute("""
    SELECT datname FROM pg_database 
    WHERE datname NOT IN ('postgres', 'template0', 'template1', 'railway')
    ORDER BY datname
""")

print("Clinic Databases:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

cursor.close()
conn.close()
```

### Drop a Clinic Database

⚠️ **Warning**: This will permanently delete all data!

```sql
-- First, disconnect all users
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'clinic_name'
  AND pid <> pg_backend_pid();

-- Then drop the database
DROP DATABASE clinic_name;
```

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to Railway database

**Solutions**:
1. Verify the TCP proxy port is correct
2. Check if Railway service is running
3. Verify firewall allows outbound connections to Railway
4. Ensure password is correct (no extra spaces)

### Database Already Exists

**Problem**: Error when creating database

**Solution**: This is normal! The system checks if the database exists first. If it does, it reuses it.

### Permission Denied

**Problem**: Cannot create databases or tables

**Solution**: Ensure your PostgreSQL user has `CREATEDB` privilege:

```sql
ALTER USER postgres CREATEDB;
```

### SSL Connection Required

**Problem**: Railway may require SSL

**Solution**: Update connection to use SSL:

```python
conn = psycopg2.connect(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    database=db,
    sslmode='require'  # Add this line
)
```

## Next Steps

1. ✓ Configure `.env` with Railway credentials
2. ✓ Run `python test_db_setup.py` to verify setup
3. ✓ Start FastAPI server: `python main.py`
4. ✓ Configure Google Apps Script with webhook URL
5. ⏳ Send test email to `developers.mxd+testclinic@gmail.com`
6. ⏳ Verify database and table creation
7. ⏳ Implement data import from Excel attachments

## Support

If you encounter issues:
1. Check the `email_logs.log` file for error messages
2. Verify environment variables are loaded correctly
3. Test database connection manually
4. Review Railway service status and logs

