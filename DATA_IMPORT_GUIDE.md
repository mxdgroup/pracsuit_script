# Data Import Guide

## Overview

The system now automatically imports appointment data from Excel files attached to emails. This document explains how the data import works and how to use it.

## How It Works

### Complete Flow

```
Email Received with Excel Attachment
    ↓
Extract Clinic Name (e.g., "supertest")
    ↓
Create/Use Database "supertest"
    ↓
Create/Use Table "appointments"
    ↓
Parse Excel File (base64 → DataFrame)
    ↓
Map Excel Columns to Database Columns
    ↓
Insert/Update Rows (UPSERT based on appointment_id)
    ↓
Return Success with row counts
```

### Key Features

1. **Automatic Data Import**: Excel data is automatically parsed and inserted
2. **No Duplicates**: Uses `appointment_id` as unique identifier
3. **Upsert Logic**: If appointment exists, it updates; if not, it inserts
4. **Batch Processing**: Efficient bulk insert for large files
5. **Null Handling**: Properly handles empty cells in Excel

## Database Schema

### Primary Key
- `id` (SERIAL): Auto-incrementing unique ID for each row

### Unique Constraint
- `appointment_id` (BIGINT UNIQUE): Prevents duplicate appointments

### Indexes
- `appointment_date`: For date-based queries
- `client_id`: For client lookups
- `appointment_id`: For unique identification

### Automatic Timestamps
- `created_at`: Set when row is first inserted
- `updated_at`: Updated every time row is modified

## Excel Column Mapping

The system automatically maps Excel columns to database columns:

| Excel Column | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| Appointment Date | appointment_date | TIMESTAMP | Date and time of appointment |
| Client | client | VARCHAR(255) | Client name |
| Appointment Type | appointment_type | VARCHAR(255) | Type of appointment |
| Profession | profession | VARCHAR(255) | Professional category |
| ClientDuration | client_duration | NUMERIC | Duration in minutes |
| Practitioner | practitioner | VARCHAR(255) | Practitioner name |
| Business | business | VARCHAR(255) | Business location |
| Appointment Status | appointment_status | VARCHAR(100) | Status (Confirmed, Cancelled, etc.) |
| Column # | column_number | NUMERIC | Column reference |
| Billed Status | billed_status | VARCHAR(100) | Billing status |
| Clinical Note | clinical_note | TEXT | Clinical notes |
| Client ID | client_id | BIGINT | Unique client identifier |
| Appointment ID | appointment_id | BIGINT | **Unique appointment identifier** |
| Address 1 | address_1 | VARCHAR(255) | Address line 1 |
| Address 2 | address_2 | VARCHAR(255) | Address line 2 |
| Address 3 | address_3 | VARCHAR(255) | Address line 3 |
| Address 4 | address_4 | VARCHAR(255) | Address line 4 |
| Suburb | suburb | VARCHAR(100) | Suburb |
| State | state | VARCHAR(100) | State |
| Postcode | postcode | VARCHAR(20) | Postal code |
| Country | country | VARCHAR(100) | Country |

## Duplicate Prevention

### How Duplicates are Handled

The system uses PostgreSQL's `ON CONFLICT` clause for **UPSERT** operations:

```sql
INSERT INTO appointments (...)
VALUES (...)
ON CONFLICT (appointment_id) 
DO UPDATE SET 
    client = EXCLUDED.client,
    appointment_date = EXCLUDED.appointment_date,
    ...
    updated_at = CURRENT_TIMESTAMP
```

**What this means:**
- If an appointment with the same `appointment_id` exists, it updates all fields
- If it doesn't exist, it inserts a new row
- The `updated_at` timestamp tracks when changes occurred

### Example Scenario

**First Email** (October 28):
```
Appointment ID: 123456
Client: John Smith
Status: Confirmed
→ Inserted as new row
```

**Second Email** (October 29) with updated data:
```
Appointment ID: 123456
Client: John Smith
Status: Cancelled
→ Updates existing row (status changes from Confirmed to Cancelled)
```

## API Response Format

When an email is processed, the API returns detailed information:

```json
{
  "status": "success",
  "message": "Email logged successfully",
  "timestamp": "2025-10-28T23:55:21.000Z",
  "saved_to": "emails/email_20251028_235521.json",
  "database_result": {
    "status": "success",
    "clinic": "supertest",
    "results": [
      {
        "filename": "Appointment Report 281025_1151PM.xlsx",
        "table": "appointments",
        "database": "supertest",
        "status": "success",
        "rows_processed": 68,
        "rows_affected": 68
      }
    ]
  }
}
```

**Key Fields:**
- `rows_processed`: Total rows read from Excel
- `rows_affected`: Rows inserted or updated in database

## Testing the Data Import

### 1. Prepare Test Email

Send an email with:
- **To**: `developers.mxd+testclinic@gmail.com`
- **Subject**: "Appointment Report"
- **Attachment**: Excel file starting with "Appointment" (e.g., `Appointment Report 281025.xlsx`)

### 2. Check Logs

Monitor `email_logs.log` for processing details:

```
INFO - Processing email for clinic: testclinic
INFO - Successfully parsed Excel file 'Appointment Report.xlsx': 68 rows, 21 columns
INFO - Successfully inserted/updated 68 appointments in database 'testclinic'
```

### 3. Verify in Database

Use the read script:

```bash
python read_db.py
```

Or query directly:

```python
from read_db import get_all_appointments

appointments = get_all_appointments('testclinic')
print(f"Total appointments: {len(appointments)}")
```

### 4. Check for Duplicates

Send the same file again and verify:
- `rows_processed`: Same as before (e.g., 68)
- `rows_affected`: 68 (all updated, not duplicated)

Then query the database:

```python
from read_db import get_db_connection

conn = get_db_connection('testclinic')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM appointments")
count = cursor.fetchone()[0]
print(f"Total rows: {count}")  # Should still be 68, not 136
cursor.close()
conn.close()
```

## Troubleshooting

### No Data Imported

**Problem**: Table created but no rows inserted

**Solutions:**
1. Check if Excel file has the correct column names
2. Verify attachment data is being sent (check logs)
3. Ensure Google Script has been updated to send base64 data
4. Check for errors in `email_logs.log`

### Column Mapping Errors

**Problem**: Error about missing columns

**Solutions:**
1. Verify Excel column names match exactly (case-sensitive)
2. Check for typos in column names
3. Ensure all required columns exist in Excel file

### Duplicate Rows

**Problem**: Same appointment appears multiple times

**Solutions:**
1. Verify `appointment_id` is unique in your Excel file
2. Check if `appointment_id` column exists and has values
3. Review database unique constraint: `SELECT * FROM appointments WHERE appointment_id = [your_id]`

### Performance Issues

**Problem**: Large files take too long to import

**Solutions:**
1. The system uses batch insert (`execute_values`) for efficiency
2. For very large files (10,000+ rows), consider:
   - Breaking into smaller files
   - Increasing database connection timeout
   - Adding more indexes if queries are slow

## Advanced Usage

### Manual Data Import

You can import Excel files manually without email:

```python
from main import parse_excel_from_base64, insert_appointments_data
import base64

# Read Excel file
with open('Appointment Report.xlsx', 'rb') as f:
    excel_data = base64.b64encode(f.read()).decode()

# Parse and insert
df = parse_excel_from_base64(excel_data, 'Appointment Report.xlsx')
result = insert_appointments_data('testclinic', df)
print(result)
```

### Custom Column Mapping

If your Excel has different column names, modify the mapping in `main.py`:

```python
# In map_excel_columns_to_db function
column_mapping = {
    'Your Column Name': 'database_column_name',
    # ... rest of mappings
}
```

### Bulk Operations

To delete and reimport all data:

```sql
-- Connect to clinic database
\c testclinic

-- Clear all appointments
TRUNCATE appointments RESTART IDENTITY;

-- Restart ID sequence
ALTER SEQUENCE appointments_id_seq RESTART WITH 1;
```

Then send the email again to reimport fresh data.

## Data Validation

The system performs basic validation:
- ✓ Checks if Excel file is parseable
- ✓ Verifies required columns exist
- ✓ Handles NULL/empty values
- ✓ Ensures appointment_id is unique

**Not validated (handled by database):**
- Data type conversions (pandas handles this)
- Date format parsing (automatic)
- Numeric conversions (automatic)

## Monitoring

### Success Metrics

Check these to ensure import is working:

1. **Email logs**: `email_logs.log`
2. **Saved emails**: `emails/` directory
3. **Database row count**: `SELECT COUNT(*) FROM appointments`
4. **Latest timestamp**: `SELECT MAX(updated_at) FROM appointments`

### Alerts to Watch For

- **Warning**: "No attachment data found"
- **Error**: "Failed to parse Excel file"
- **Error**: "Failed to create table"
- **Error**: "Error inserting appointments data"

## Next Steps

1. ✓ Set up your email forwarding (Google Script)
2. ✓ Configure database connection (Railway)
3. ✓ Test with sample email
4. ✓ Verify data appears in database
5. ⏳ Set up automated reporting
6. ⏳ Add more table types (invoices, clients, etc.)

