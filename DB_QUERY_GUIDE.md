# Database Query Guide

## Quick Start

The `read_db.py` script provides two modes for reading data from your clinic databases:

### 1. Automatic Demo Mode (Default)

Shows a quick overview of your database:

```bash
python read_db.py
```

**Output:**
- Lists all clinic databases
- Shows table information
- Displays appointment statistics
- Shows recent appointments
- Exports sample data to JSON

### 2. Interactive Mode

Full-featured interactive query system:

```bash
python read_db.py --interactive
```

**Features:**
- Browse appointments
- Search by client, practitioner, date
- View statistics
- Export data to JSON
- Free text search across all fields

## Available Functions

### List All Clinics

```python
from read_db import list_all_clinics

clinics = list_all_clinics()
print(clinics)  # ['supertest', 'testclinic', 'demo_clinic']
```

### Get All Appointments

```python
from read_db import get_all_appointments

appointments = get_all_appointments('supertest', limit=50)
for apt in appointments:
    print(apt['client'], apt['appointment_date'])
```

### Search by Client

```python
from read_db import get_appointments_by_client

appointments = get_appointments_by_client('supertest', 'John')
# Returns all appointments for clients with 'John' in their name
```

### Search by Practitioner

```python
from read_db import get_appointments_by_practitioner

appointments = get_appointments_by_practitioner('supertest', 'Dr. Smith')
# Returns all appointments for practitioners with 'Dr. Smith' in their name
```

### Search by Date Range

```python
from read_db import get_appointments_by_date

# Single date (all appointments from this date forward)
appointments = get_appointments_by_date('supertest', '2025-10-01')

# Date range
appointments = get_appointments_by_date('supertest', '2025-10-01', '2025-10-31')
```

### Get Statistics

```python
from read_db import get_appointment_statistics

stats = get_appointment_statistics('supertest')
print(stats['total_appointments'])
print(stats['by_status'])
print(stats['top_practitioners'])
```

### Free Text Search

```python
from read_db import search_appointments

# Search across client, practitioner, type, business, and notes
appointments = search_appointments('supertest', 'massage')
```

### Export to JSON

```python
from read_db import export_to_json, get_all_appointments

appointments = get_all_appointments('supertest', limit=1000)
export_to_json(appointments, 'my_appointments.json')
```

## Interactive Mode Menu

When you run in interactive mode, you'll see:

```
Query Options:
  1. Show all appointments (limit 10)
  2. Search by client name
  3. Search by practitioner name
  4. Search by date range
  5. Show statistics
  6. Free text search
  7. Export all appointments to JSON
  0. Exit
```

### Example Session

```
$ python read_db.py --interactive

INTERACTIVE DATABASE QUERY MODE
================================================================================

Available clinics:
  1. supertest
  2. testclinic

Select clinic number (or 0 to exit): 1

Selected clinic: supertest

Query Options:
  1. Show all appointments (limit 10)
  2. Search by client name
  ...

Select option: 2

Enter client name: Michelle
Found 1 appointments for 'Michelle':

================================================================================
Appointment ID: 123456
Date: 2025-10-28 07:30:00
Client: Michelle Kim Davies (ID: 789)
Practitioner: Dr. Smith
Type: Consultation
Status: Confirmed
Duration: 30.0 min
Business: Main Clinic
================================================================================
```

## Custom Python Scripts

You can create your own scripts using the functions:

```python
# my_custom_query.py
from read_db import get_db_connection
from psycopg2.extras import RealDictCursor

clinic_name = 'supertest'
conn = get_db_connection(clinic_name)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Custom query
cursor.execute("""
    SELECT 
        DATE(appointment_date) as date,
        COUNT(*) as total_appointments,
        COUNT(DISTINCT client_id) as unique_clients
    FROM appointments
    WHERE appointment_status = 'Confirmed'
    GROUP BY DATE(appointment_date)
    ORDER BY date DESC
    LIMIT 30
""")

results = cursor.fetchall()
for row in results:
    print(f"{row['date']}: {row['total_appointments']} appointments, {row['unique_clients']} clients")

cursor.close()
conn.close()
```

## Common Queries

### 1. Today's Appointments

```python
from read_db import get_appointments_by_date
from datetime import date

today = date.today().isoformat()
appointments = get_appointments_by_date('supertest', today, today)
```

### 2. Upcoming Appointments

```python
from read_db import get_appointments_by_date
from datetime import date

today = date.today().isoformat()
appointments = get_appointments_by_date('supertest', today)
```

### 3. Cancelled Appointments

```python
from read_db import get_db_connection
from psycopg2.extras import RealDictCursor

conn = get_db_connection('supertest')
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT * FROM appointments 
    WHERE appointment_status = 'Cancelled'
    ORDER BY appointment_date DESC
""")

cancelled = cursor.fetchall()
cursor.close()
conn.close()
```

### 4. Appointments by Location/Business

```python
from read_db import get_db_connection
from psycopg2.extras import RealDictCursor

conn = get_db_connection('supertest')
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT business, COUNT(*) as total
    FROM appointments
    GROUP BY business
    ORDER BY total DESC
""")

by_business = cursor.fetchall()
cursor.close()
conn.close()
```

## Tips

1. **Export First, Query Later**: Use option 7 in interactive mode to export all data, then query the JSON file locally

2. **Date Format**: Always use `YYYY-MM-DD` format for dates (e.g., `2025-10-28`)

3. **Partial Matches**: Client and practitioner searches use `ILIKE` (case-insensitive) with wildcards, so "john" will match "John Smith"

4. **Performance**: Use `LIMIT` for large datasets to avoid long query times

5. **JSON Export**: Exported JSON files include all fields and can be imported into Excel, Google Sheets, or analyzed with pandas

## Troubleshooting

### "No clinic databases found"
- Make sure you've processed at least one email with an attachment
- Verify your FastAPI server received the email webhook
- Check `email_logs.log` for processing errors

### Connection errors
- Verify your `.env` file has the correct Railway credentials
- Run `python test_db_setup.py` to test the connection

### Empty results
- The appointments table exists but may not have data yet
- Data import from Excel attachments needs to be implemented (coming next)
- For now, you can manually insert test data using SQL

## Next: Data Import

Currently, the system only creates the database structure. To automatically import Excel data from email attachments, run the data import script (to be created).

