"""
Script to read data from PostgreSQL clinic databases
Demonstrates various queries and data retrieval methods
"""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'admin_db': os.getenv('POSTGRES_ADMIN_DB', 'postgres')
}


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


def list_all_clinics():
    """List all clinic databases (excluding system databases)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datname NOT IN ('postgres', 'template0', 'template1', 'railway')
            ORDER BY datname
        """)
        
        clinics = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return clinics
    except Exception as e:
        print(f"Error listing clinics: {e}")
        return []


def get_table_info(clinic_name: str, table_name: str = 'appointments'):
    """Get information about a table in a clinic database"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor()
        
        # Get column information
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'columns': columns,
            'row_count': row_count
        }
    except Exception as e:
        print(f"Error getting table info: {e}")
        return None


def list_all_tables_in_database(clinic_name: str):
    """List all tables in a clinic database with row counts"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor()
        
        # Get all tables in the public schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = []
        for row in cursor.fetchall():
            table_name = row[0]
            
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            tables.append({
                'table_name': table_name,
                'row_count': row_count
            })
        
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        print(f"Error listing tables in database '{clinic_name}': {e}")
        return []


def get_all_databases_summary():
    """Get a summary of all clinic databases with table and row counts"""
    try:
        clinics = list_all_clinics()
        summary = []
        
        for clinic_name in clinics:
            tables = list_all_tables_in_database(clinic_name)
            total_rows = sum(table['row_count'] for table in tables)
            
            summary.append({
                'database': clinic_name,
                'tables': tables,
                'total_tables': len(tables),
                'total_rows': total_rows
            })
        
        return summary
    except Exception as e:
        print(f"Error getting database summary: {e}")
        return []


def get_all_appointments(clinic_name: str, limit: int = 100):
    """Get all appointments from a clinic database"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(f"""
            SELECT * FROM appointments 
            ORDER BY appointment_date DESC 
            LIMIT {limit}
        """)
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return appointments
    except Exception as e:
        print(f"Error getting appointments: {e}")
        return []


def get_appointments_by_date(clinic_name: str, start_date: str, end_date: str = None):
    """Get appointments within a date range"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if end_date:
            cursor.execute("""
                SELECT * FROM appointments 
                WHERE appointment_date BETWEEN %s AND %s
                ORDER BY appointment_date
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT * FROM appointments 
                WHERE appointment_date >= %s
                ORDER BY appointment_date
            """, (start_date,))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return appointments
    except Exception as e:
        print(f"Error getting appointments by date: {e}")
        return []


def get_appointments_by_client(clinic_name: str, client_name: str):
    """Get all appointments for a specific client"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE client ILIKE %s
            ORDER BY appointment_date DESC
        """, (f'%{client_name}%',))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return appointments
    except Exception as e:
        print(f"Error getting appointments by client: {e}")
        return []


def get_appointments_by_practitioner(clinic_name: str, practitioner_name: str):
    """Get all appointments for a specific practitioner"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE practitioner ILIKE %s
            ORDER BY appointment_date DESC
        """, (f'%{practitioner_name}%',))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return appointments
    except Exception as e:
        print(f"Error getting appointments by practitioner: {e}")
        return []


def get_appointment_statistics(clinic_name: str):
    """Get statistics about appointments in a clinic"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total appointments
        cursor.execute("SELECT COUNT(*) FROM appointments")
        stats['total_appointments'] = cursor.fetchone()[0]
        
        # Appointments by status
        cursor.execute("""
            SELECT appointment_status, COUNT(*) 
            FROM appointments 
            GROUP BY appointment_status
        """)
        stats['by_status'] = dict(cursor.fetchall())
        
        # Appointments by practitioner
        cursor.execute("""
            SELECT practitioner, COUNT(*) 
            FROM appointments 
            GROUP BY practitioner
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        stats['top_practitioners'] = dict(cursor.fetchall())
        
        # Appointments by type
        cursor.execute("""
            SELECT appointment_type, COUNT(*) 
            FROM appointments 
            GROUP BY appointment_type
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        stats['top_types'] = dict(cursor.fetchall())
        
        # Date range
        cursor.execute("""
            SELECT 
                MIN(appointment_date) as earliest,
                MAX(appointment_date) as latest
            FROM appointments
        """)
        date_range = cursor.fetchone()
        stats['date_range'] = {
            'earliest': date_range[0],
            'latest': date_range[1]
        }
        
        cursor.close()
        conn.close()
        
        return stats
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}


def search_appointments(clinic_name: str, search_term: str):
    """Search appointments across multiple fields"""
    try:
        conn = get_db_connection(clinic_name)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE 
                client ILIKE %s OR
                practitioner ILIKE %s OR
                appointment_type ILIKE %s OR
                business ILIKE %s OR
                clinical_note ILIKE %s
            ORDER BY appointment_date DESC
            LIMIT 100
        """, tuple([f'%{search_term}%'] * 5))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return appointments
    except Exception as e:
        print(f"Error searching appointments: {e}")
        return []


def export_to_json(data, filename: str):
    """Export data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Data exported to: {filename}")
        return True
    except Exception as e:
        print(f"Error exporting to JSON: {e}")
        return False


def print_appointment(appointment):
    """Pretty print a single appointment"""
    print("\n" + "="*80)
    print(f"Appointment ID: {appointment.get('appointment_id')}")
    print(f"Date: {appointment.get('appointment_date')}")
    print(f"Client: {appointment.get('client')} (ID: {appointment.get('client_id')})")
    print(f"Practitioner: {appointment.get('practitioner')}")
    print(f"Type: {appointment.get('appointment_type')}")
    print(f"Status: {appointment.get('appointment_status')}")
    print(f"Duration: {appointment.get('client_duration')} min")
    print(f"Business: {appointment.get('business')}")
    if appointment.get('clinical_note'):
        print(f"Note: {appointment.get('clinical_note')}")
    print("="*80)


def main():
    """Main function to demonstrate database reading"""
    print("=" * 80)
    print("PostgreSQL Database Reader - Complete Overview")
    print("=" * 80)
    
    # Get complete database summary
    print("\n[DATABASE SUMMARY]")
    print("-" * 80)
    
    summary = get_all_databases_summary()
    
    if not summary:
        print("  No clinic databases found.")
        print("\n  Note: Clinic databases are created when emails are processed.")
        print("  Send a test email to developers.mxd+testclinic@gmail.com")
        return
    
    # Display summary for all databases
    total_databases = len(summary)
    total_tables_all = sum(db['total_tables'] for db in summary)
    total_rows_all = sum(db['total_rows'] for db in summary)
    
    print(f"\nTotal Clinic Databases: {total_databases}")
    print(f"Total Tables Across All Databases: {total_tables_all}")
    print(f"Total Rows Across All Databases: {total_rows_all}")
    print("\n" + "-" * 80)
    
    # Display detailed information for each database
    for idx, db_info in enumerate(summary, 1):
        print(f"\n[{idx}] Database: {db_info['database']}")
        print(f"    Tables: {db_info['total_tables']}")
        print(f"    Total Rows: {db_info['total_rows']}")
        
        if db_info['tables']:
            print(f"\n    Table Details:")
            for table in db_info['tables']:
                print(f"      - {table['table_name']:<30} {table['row_count']:>10,} rows")
        else:
            print(f"    No tables found in this database")
        
        print("    " + "-" * 76)
    
    # Detailed analysis of first database (if exists)
    if summary:
        clinic_name = summary[0]['database']
        print(f"\n\n[DETAILED ANALYSIS: {clinic_name}]")
        print("-" * 80)
        
        # Get statistics
        print(f"\nAppointment Statistics:")
        stats = get_appointment_statistics(clinic_name)
        if stats:
            print(f"  Total appointments: {stats.get('total_appointments', 0):,}")
            
            if stats.get('by_status'):
                print("\n  By Status:")
                for status, count in stats['by_status'].items():
                    status_display = status if status else "(No Status)"
                    print(f"    - {status_display:<30} {count:>5,} appointments")
            
            if stats.get('top_practitioners'):
                print("\n  Top 5 Practitioners:")
                for i, (practitioner, count) in enumerate(list(stats['top_practitioners'].items())[:5], 1):
                    print(f"    {i}. {practitioner:<35} {count:>5,} appointments")
            
            if stats.get('top_types'):
                print("\n  Top 5 Appointment Types:")
                for i, (apt_type, count) in enumerate(list(stats['top_types'].items())[:5], 1):
                    print(f"    {i}. {apt_type:<35} {count:>5,} appointments")
            
            if stats.get('date_range'):
                print(f"\n  Date Range:")
                print(f"    Earliest: {stats['date_range']['earliest']}")
                print(f"    Latest:   {stats['date_range']['latest']}")
        
        # Get recent appointments
        print(f"\n\nRecent Appointments (last 3):")
        print("-" * 80)
        appointments = get_all_appointments(clinic_name, limit=3)
        if appointments:
            for appointment in appointments:
                print_appointment(appointment)
            
            # Export to JSON
            print(f"\n[EXPORT] Saving sample to JSON...")
            export_to_json(appointments, f'appointments_{clinic_name}_sample.json')
        else:
            print("  No appointments found.")
    
    print("\n" + "=" * 80)
    print("Query completed!")
    print("=" * 80)
    print("\nTip: Run 'python read_db.py --interactive' for interactive query mode")


# Interactive mode functions
def interactive_mode():
    """Interactive mode for querying the database"""
    print("\n" + "=" * 80)
    print("INTERACTIVE DATABASE QUERY MODE")
    print("=" * 80)
    
    # Get clinics
    clinics = list_all_clinics()
    if not clinics:
        print("No clinic databases found.")
        return
    
    print("\nAvailable clinics:")
    for i, clinic in enumerate(clinics, 1):
        print(f"  {i}. {clinic}")
    
    try:
        choice = int(input("\nSelect clinic number (or 0 to exit): "))
        if choice == 0 or choice > len(clinics):
            return
        
        clinic_name = clinics[choice - 1]
        print(f"\nSelected clinic: {clinic_name}")
        
        while True:
            print("\n" + "-" * 80)
            print("Query Options:")
            print("  1. Show all appointments (limit 10)")
            print("  2. Search by client name")
            print("  3. Search by practitioner name")
            print("  4. Search by date range")
            print("  5. Show statistics")
            print("  6. Free text search")
            print("  7. Export all appointments to JSON")
            print("  0. Exit")
            print("-" * 80)
            
            option = input("\nSelect option: ")
            
            if option == '0':
                break
            elif option == '1':
                appointments = get_all_appointments(clinic_name, limit=10)
                print(f"\nFound {len(appointments)} appointments:")
                for apt in appointments:
                    print_appointment(apt)
            
            elif option == '2':
                client_name = input("Enter client name: ")
                appointments = get_appointments_by_client(clinic_name, client_name)
                print(f"\nFound {len(appointments)} appointments for '{client_name}':")
                for apt in appointments:
                    print_appointment(apt)
            
            elif option == '3':
                practitioner_name = input("Enter practitioner name: ")
                appointments = get_appointments_by_practitioner(clinic_name, practitioner_name)
                print(f"\nFound {len(appointments)} appointments for '{practitioner_name}':")
                for apt in appointments:
                    print_appointment(apt)
            
            elif option == '4':
                start_date = input("Enter start date (YYYY-MM-DD): ")
                end_date = input("Enter end date (YYYY-MM-DD) or press Enter for all after start: ")
                appointments = get_appointments_by_date(clinic_name, start_date, end_date if end_date else None)
                print(f"\nFound {len(appointments)} appointments:")
                for apt in appointments:
                    print_appointment(apt)
            
            elif option == '5':
                stats = get_appointment_statistics(clinic_name)
                print("\nStatistics:")
                print(json.dumps(stats, indent=2, default=str))
            
            elif option == '6':
                search_term = input("Enter search term: ")
                appointments = search_appointments(clinic_name, search_term)
                print(f"\nFound {len(appointments)} appointments matching '{search_term}':")
                for apt in appointments:
                    print_appointment(apt)
            
            elif option == '7':
                appointments = get_all_appointments(clinic_name, limit=10000)
                filename = f'appointments_{clinic_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                export_to_json(appointments, filename)
            
            else:
                print("Invalid option. Please try again.")
    
    except ValueError:
        print("Invalid input.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        main()
        print("\nTip: Run 'python read_db.py --interactive' for interactive query mode")

