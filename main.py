from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
from datetime import datetime
from pathlib import Path
import re
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values
import pandas as pd
import base64
import io

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
import sys

# File handler with UTF-8 encoding
file_handler = logging.FileHandler('email_logs.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Console handler with UTF-8 encoding and error handling for Windows
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# Set UTF-8 encoding on stdout to handle Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'admin_db': os.getenv('POSTGRES_ADMIN_DB', 'postgres')
}


def extract_clinic_name(email_address: str) -> str:
    """
    Extract clinic name from email address between + and @
    Example: developers.mxd+supertest@gmail.com -> supertest
    """
    match = re.search(r'\+([^@]+)@', email_address)
    if match:
        clinic_name = match.group(1).lower()
        # Sanitize database name (only alphanumeric and underscore)
        clinic_name = re.sub(r'[^a-z0-9_]', '_', clinic_name)
        return clinic_name
    return None


def extract_table_name(filename: str) -> str:
    """
    Extract table name from filename (first word)
    Example: "Appointment Report 281025_1151PM.xlsx" -> "appointments"
    """
    # Get first word from filename
    first_word = filename.split()[0] if filename else ""
    # Convert to lowercase and add 's' if not already plural
    table_name = first_word.lower()
    if table_name and not table_name.endswith('s'):
        table_name += 's'
    return table_name


def get_db_connection(database_name: str = None):
    """Get a connection to the specified database or admin database"""
    db = database_name or DB_CONFIG['admin_db']
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=db
    )


def database_exists(database_name: str) -> bool:
    """Check if database exists"""
    try:
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database_name,)
        )
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Error checking database existence: {e}")
        return False


def create_database(database_name: str):
    """Create a new database if it doesn't exist"""
    try:
        if database_exists(database_name):
            logger.info(f"Database '{database_name}' already exists")
            return True
        
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f'CREATE DATABASE {database_name}')
        logger.info(f"Database '{database_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False


def create_appointments_table(database_name: str):
    """Create appointments table in the specified database"""
    try:
        conn = get_db_connection(database_name)
        cursor = conn.cursor()
        
        # Create appointments table with schema matching Excel structure
        create_table_query = """
        CREATE TABLE IF NOT EXISTS appointments (
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
        )
        """
        
        cursor.execute(create_table_query)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_date 
            ON appointments(appointment_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_client_id 
            ON appointments(client_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_appointment_id 
            ON appointments(appointment_id)
        """)
        
        conn.commit()
        logger.info(f"Appointments table created successfully in database '{database_name}'")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating appointments table: {e}")
        return False


def parse_excel_from_base64(base64_data: str, filename: str):
    """Parse Excel file from base64 encoded data"""
    try:
        # Decode base64 data
        excel_bytes = base64.b64decode(base64_data)
        
        # Read Excel file into pandas DataFrame
        df = pd.read_excel(io.BytesIO(excel_bytes))
        
        logger.info(f"Successfully parsed Excel file '{filename}': {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Error parsing Excel file '{filename}': {e}")
        return None


def map_excel_columns_to_db(df: pd.DataFrame):
    """Map Excel column names to database column names"""
    # Column mapping from Excel to database
    column_mapping = {
        'Appointment Date': 'appointment_date',
        'Client': 'client',
        'Appointment Type': 'appointment_type',
        'Profession': 'profession',
        'ClientDuration': 'client_duration',
        'Practitioner': 'practitioner',
        'Business': 'business',
        'Appointment Status': 'appointment_status',
        'Column #': 'column_number',
        'Billed Status': 'billed_status',
        'Clinical Note': 'clinical_note',
        'Client ID': 'client_id',
        'Appointment ID': 'appointment_id',
        'Address 1': 'address_1',
        'Address 2': 'address_2',
        'Address 3': 'address_3',
        'Address 4': 'address_4',
        'Suburb': 'suburb',
        'State': 'state',
        'Postcode': 'postcode',
        'Country': 'country'
    }
    
    # Rename columns
    df_mapped = df.rename(columns=column_mapping)
    
    # Convert NaN to None for proper NULL handling in PostgreSQL
    df_mapped = df_mapped.where(pd.notna(df_mapped), None)
    
    return df_mapped


def insert_appointments_data(database_name: str, df: pd.DataFrame):
    """Insert appointment data into the database with upsert to avoid duplicates"""
    try:
        conn = get_db_connection(database_name)
        cursor = conn.cursor()
        
        # Map columns
        df_mapped = map_excel_columns_to_db(df)
        
        # Prepare columns list (excluding id, created_at, updated_at which are auto-generated)
        db_columns = [
            'appointment_date', 'client', 'appointment_type', 'profession',
            'client_duration', 'practitioner', 'business', 'appointment_status',
            'column_number', 'billed_status', 'clinical_note', 'client_id',
            'appointment_id', 'address_1', 'address_2', 'address_3', 'address_4',
            'suburb', 'state', 'postcode', 'country'
        ]
        
        # Prepare data tuples
        data_tuples = []
        for _, row in df_mapped.iterrows():
            row_data = tuple(row[col] if col in row else None for col in db_columns)
            data_tuples.append(row_data)
        
        # Prepare INSERT ... ON CONFLICT (UPSERT) query
        # This will insert new records or update existing ones based on appointment_id
        columns_str = ', '.join(db_columns)
        placeholders = ', '.join(['%s'] * len(db_columns))
        
        # Build update columns for ON CONFLICT (excluding appointment_id which is the conflict target)
        update_columns = [col for col in db_columns if col != 'appointment_id']
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        
        upsert_query = f"""
        INSERT INTO appointments ({columns_str})
        VALUES %s
        ON CONFLICT (appointment_id) 
        DO UPDATE SET 
            {update_str},
            updated_at = CURRENT_TIMESTAMP
        """
        
        # Execute batch insert with execute_values for better performance
        execute_values(cursor, upsert_query, data_tuples)
        
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f"Successfully inserted/updated {rows_affected} appointments in database '{database_name}'")
        
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'rows_processed': len(data_tuples),
            'rows_affected': rows_affected
        }
        
    except Exception as e:
        logger.error(f"Error inserting appointments data: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def process_attachment_and_store(email_data: dict):
    """
    Process email attachments and store data in appropriate database
    """
    try:
        # Extract clinic name from 'to' field
        to_email = email_data.get('to', '')
        clinic_name = extract_clinic_name(to_email)
        
        if not clinic_name:
            logger.warning(f"Could not extract clinic name from email: {to_email}")
            return {"status": "error", "message": "Invalid email format"}
        
        logger.info(f"Processing email for clinic: {clinic_name}")
        
        # Create database for clinic
        if not create_database(clinic_name):
            return {"status": "error", "message": "Failed to create database"}
        
        # Process attachments
        attachments = email_data.get('attachments', [])
        if not attachments:
            logger.info("No attachments found in email")
            return {"status": "warning", "message": "No attachments to process"}
        
        results = []
        for attachment in attachments:
            filename = attachment.get('name', '')
            table_name = extract_table_name(filename)
            
            logger.info(f"Processing attachment: {filename} -> table: {table_name}")
            
            # Only process appointments for now
            if table_name == 'appointments':
                # Create the appointments table
                if not create_appointments_table(clinic_name):
                    results.append({
                        "filename": filename,
                        "table": table_name,
                        "database": clinic_name,
                        "status": "error",
                        "message": "Failed to create table"
                    })
                    continue
                
                # Check if attachment has data
                attachment_data = attachment.get('data', '')
                if not attachment_data:
                    logger.warning(f"No data found in attachment: {filename}")
                    results.append({
                        "filename": filename,
                        "table": table_name,
                        "database": clinic_name,
                        "status": "warning",
                        "message": "No attachment data found"
                    })
                    continue
                
                # Parse Excel file
                df = parse_excel_from_base64(attachment_data, filename)
                if df is None or df.empty:
                    results.append({
                        "filename": filename,
                        "table": table_name,
                        "database": clinic_name,
                        "status": "error",
                        "message": "Failed to parse Excel file or file is empty"
                    })
                    continue
                
                # Insert data into database
                insert_result = insert_appointments_data(clinic_name, df)
                
                if insert_result['success']:
                    results.append({
                        "filename": filename,
                        "table": table_name,
                        "database": clinic_name,
                        "status": "success",
                        "rows_processed": insert_result['rows_processed'],
                        "rows_affected": insert_result['rows_affected']
                    })
                    logger.info(f"Successfully imported {insert_result['rows_affected']} rows from {filename}")
                else:
                    results.append({
                        "filename": filename,
                        "table": table_name,
                        "database": clinic_name,
                        "status": "error",
                        "message": insert_result.get('error', 'Unknown error')
                    })
            else:
                logger.info(f"Skipping non-appointment file: {filename}")
                results.append({
                    "filename": filename,
                    "table": table_name,
                    "status": "skipped",
                    "reason": "Only appointments are processed currently"
                })
        
        return {
            "status": "success",
            "clinic": clinic_name,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing attachment: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


app = FastAPI(title="Email Forwarding Logger", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Email Logger API is running", "status": "active"}


@app.post("/webhook/email")
async def receive_email(request: Request):
    """
    Endpoint to receive email data from Google Apps Script
    Logs the complete email structure
    """
    try:
        # Get the raw body
        body = await request.body()
        
        # Try to parse as JSON
        try:
            email_data = await request.json()
            logger.info("=" * 80)
            logger.info("NEW EMAIL RECEIVED")
            logger.info("=" * 80)
            
            # Log the entire structure
            logger.info("Complete Email Structure:")
            logger.info(json.dumps(email_data, indent=2, default=str))
            
            # Log specific fields if they exist
            if isinstance(email_data, dict):
                logger.info("\n--- Email Details ---")
                logger.info(f"From: {email_data.get('from', 'N/A')}")
                logger.info(f"To: {email_data.get('to', 'N/A')}")
                logger.info(f"Subject: {email_data.get('subject', 'N/A')}")
                logger.info(f"Date: {email_data.get('date', 'N/A')}")
                logger.info(f"Body Length: {len(email_data.get('body', ''))}")
                
                if 'attachments' in email_data:
                    logger.info(f"Attachments: {len(email_data.get('attachments', []))}")
                    for idx, att in enumerate(email_data.get('attachments', [])):
                        logger.info(f"  Attachment {idx + 1}: {att.get('name', 'N/A')} ({att.get('size', 'N/A')} bytes)")
            
            logger.info("=" * 80)
            
            # Also save to a JSON file for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = Path(f"emails/email_{timestamp}.json")
            json_file.parent.mkdir(exist_ok=True)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, indent=2, default=str)
            
            logger.info(f"Email data saved to: {json_file}")
            
            # Process attachments and create database/tables
            db_result = process_attachment_and_store(email_data)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Email logged successfully",
                    "timestamp": datetime.now().isoformat(),
                    "saved_to": str(json_file),
                    "database_result": db_result
                }
            )
            
        except json.JSONDecodeError:
            # If not JSON, log the raw body
            logger.warning("Received non-JSON data:")
            logger.info(f"Raw body: {body.decode('utf-8', errors='replace')}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "warning",
                    "message": "Received non-JSON data, logged as raw text",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

