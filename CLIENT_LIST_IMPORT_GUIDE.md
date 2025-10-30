# Client List Import Guide

## Overview
The system now supports importing **two types of Excel reports** from PracSuite:

1. **Appointment Reports** → `appointments` table
2. **Client List Reports** → `clients` table

## How It Works

### 1. Email Address Detection
The system extracts the database name from the email's "To" field by looking for the pattern `email+DBNAME@domain.com`:

**Examples:**
- `matt+clinic27reporting@mxd.digital` → Database: `clinic27reporting`
- `developers.mxd+supertest@gmail.com` → Database: `supertest`

### 2. Report Type Detection
The system detects the report type from the Excel filename:

| Filename Starts With | Target Table | Example |
|---------------------|--------------|---------|
| `Appointment` | `appointments` | `Appointment Report 281025_1151PM.xlsx` |
| `Client List` | `clients` | `Client List Report 291025_0710PM.xlsx` |

### 3. Automatic Processing
When an email arrives with attachments:
1. ✅ Extracts database name from "To" field
2. ✅ Creates database if it doesn't exist
3. ✅ Detects report type from filename
4. ✅ Creates appropriate table (appointments or clients)
5. ✅ Imports data with **upsert logic** (updates existing records)
6. ✅ Logs all actions to console and file

## Client List Report Schema

The `clients` table includes 44 columns matching the PracSuite export:

### Personal Information
- `title`, `first_name`, `preferred_name`, `middle`, `surname`
- `date_of_birth`, `gender`, `pronouns`, `sex`

### Contact Details
- `address_line_1`, `address_line_2`, `address_line_3`, `address_line_4`
- `country`, `state`, `suburb`, `postcode`
- `preferred_phone`, `work_phone`, `home_phone`, `mobile`, `fax`
- `email`

### Medical & Insurance
- `medicare_no`, `medicare_irn`, `medicare_expiry`
- `dva_no`, `dva_type`
- `concession_no`, `concession_expiry`
- `health_fund`, `health_fund_member_no`
- `ndis_no`
- `gp_name`

### Practice Management
- `file_no` - Internal file number
- `client_id` - **Unique identifier** (used for upsert)
- `archived` - Archive status (Y/N)
- `notes` - Client notes
- `warnings` - Client warnings
- `fee_category` - Fee category/package
- `practitioner` - Assigned practitioner

### Dates
- `created_date` - When client was created in PracSuite
- `consent_date` - Consent date
- `privacy_policy_date` - Privacy policy acceptance date
- `db_created_at` - When record was created in database
- `db_updated_at` - When record was last updated in database

## Upsert Logic

Both tables use **upsert logic** to prevent duplicates:

- **Appointments**: Uses `appointment_id` as the unique key
  - If `appointment_id` exists → **update** the record
  - If `appointment_id` doesn't exist → **insert** new record

- **Clients**: Uses `client_id` as the unique key
  - If `client_id` exists → **update** the record
  - If `client_id` doesn't exist → **insert** new record

This means you can send the same report multiple times, and it will only update existing records rather than creating duplicates.

## Database Queries

### View All Clients
```sql
SELECT * FROM clients ORDER BY surname, first_name;
```

### Search by Name
```sql
SELECT * FROM clients 
WHERE surname ILIKE '%smith%' 
   OR first_name ILIKE '%john%';
```

### Find Clients by Practitioner
```sql
SELECT * FROM clients 
WHERE practitioner LIKE '%Dr Rin Choi%'
ORDER BY surname;
```

### Active Clients (Not Archived)
```sql
SELECT * FROM clients 
WHERE archived = 'N' OR archived IS NULL
ORDER BY surname;
```

### Clients with Warnings
```sql
SELECT first_name, surname, warnings, notes
FROM clients 
WHERE warnings IS NOT NULL AND warnings != ''
ORDER BY surname;
```

### Clients by Fee Category
```sql
SELECT fee_category, COUNT(*) as client_count
FROM clients 
GROUP BY fee_category
ORDER BY client_count DESC;
```

### Recent Clients (Created in Last 30 Days)
```sql
SELECT * FROM clients 
WHERE created_date >= NOW() - INTERVAL '30 days'
ORDER BY created_date DESC;
```

### Join Clients with Appointments
```sql
SELECT 
    c.first_name,
    c.surname,
    c.email,
    c.mobile,
    a.appointment_date,
    a.appointment_type,
    a.practitioner,
    a.appointment_status
FROM clients c
LEFT JOIN appointments a ON c.client_id = a.client_id
WHERE c.client_id = 2711098  -- Specific client
ORDER BY a.appointment_date DESC;
```

## Testing

### Test with Sample Data
1. Make sure the server is running:
   ```bash
   python main.py
   ```

2. Check the logs - you should see:
   ```
   Processing email for clinic: clinic27reporting
   Database 'clinic27reporting' already exists
   Processing attachment: Client List Report 291025_0710PM.xlsx -> table: clients
   Clients table created successfully in database 'clinic27reporting'
   Successfully parsed Excel file: 79 rows, 44 columns
   Successfully inserted/updated 79 clients in database 'clinic27reporting'
   ```

### Verify Import
```bash
python read_db.py clinic27reporting
```

You should see both tables:
- `appointments` (if you've imported appointment data)
- `clients` (with 79 records from the sample file)

## Troubleshooting

### Issue: "Could not extract clinic name from email"
**Solution**: Ensure the "To" email contains a `+` followed by the database name:
- ✅ `matt+clinic27reporting@mxd.digital`
- ❌ `matt@mxd.digital`

### Issue: "Skipping unsupported file"
**Solution**: Ensure the filename starts with either:
- `Appointment` (for appointment reports)
- `Client List` (for client list reports)

### Issue: "Failed to parse Excel file"
**Solution**: 
- Verify the Excel file is valid and not corrupted
- Check the attachment is properly base64 encoded
- Ensure it's an `.xlsx` file (not `.xls` or other formats)

### Issue: Duplicate client records
**Solution**: This shouldn't happen due to upsert logic. Check:
- Is `client_id` populated in the Excel file?
- Run: `SELECT client_id, COUNT(*) FROM clients GROUP BY client_id HAVING COUNT(*) > 1;`

## Summary

The system now automatically:
1. ✅ Detects database name from email address
2. ✅ Creates separate databases for each clinic
3. ✅ Imports both Appointment and Client List reports
4. ✅ Prevents duplicates with upsert logic
5. ✅ Maintains full data history
6. ✅ Supports querying and reporting

All data is stored in PostgreSQL and can be queried using standard SQL or connected to BI tools like Grafana, Metabase, or Power BI.

