"""
Demo Script: Populate Vehicle Health Analytics Test Data

This script adds sample mileage data to existing vehicles
to demonstrate the AI-powered health analytics feature.
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
import random

# Database connection
DB_HOST = "localhost"
DB_NAME = "vehicle_service"
DB_USER = "postgres"
DB_PASS = "password"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=DictCursor
    )
    return conn

def populate_mileage_data():
    """Add realistic mileage data to vehicles"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all vehicles
    cursor.execute("SELECT id, year FROM vehicles")
    vehicles = cursor.fetchall()
    
    print(f"Found {len(vehicles)} vehicles")
    
    for vehicle in vehicles:
        vehicle_id = vehicle['id']
        vehicle_year = vehicle['year'] or 2020
        
        # Calculate realistic mileage based on vehicle age
        vehicle_age = datetime.now().year - vehicle_year
        
        # Average 12,000-15,000 km per year for normal usage
        # Some vehicles will have higher usage
        usage_factor = random.choice([0.8, 1.0, 1.2, 1.5, 1.8])  # Variation in usage
        avg_yearly_km = 13000 * usage_factor
        
        current_mileage = int(vehicle_age * avg_yearly_km)
        
        # Add some randomness
        current_mileage += random.randint(-2000, 5000)
        current_mileage = max(0, current_mileage)  # Ensure non-negative
        
        # Update vehicle mileage
        cursor.execute("""
            UPDATE vehicles 
            SET current_mileage = %s, 
                last_mileage_update = %s 
            WHERE id = %s
        """, (current_mileage, datetime.now().strftime('%Y-%m-%d'), vehicle_id))
        
        print(f"  Vehicle ID {vehicle_id}: {current_mileage:,} km (Age: {vehicle_age} years, Factor: {usage_factor:.1f}x)")
    
    conn.commit()
    conn.close()
    print("\n✅ Mileage data populated successfully!")

def add_sample_service_history():
    """Add some sample service records for better health analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get vehicles without much service history
    cursor.execute("""
        SELECT v.id, v.owner_id, COUNT(s.id) as service_count
        FROM vehicles v
        LEFT JOIN services s ON v.id = s.vehicle_id
        GROUP BY v.id, v.owner_id
        HAVING COUNT(s.id) < 3
        LIMIT 5
    """)
    vehicles = cursor.fetchall()
    
    if len(vehicles) == 0:
        print("All vehicles have sufficient service history")
        conn.close()
        return
    
    print(f"\nAdding sample services to {len(vehicles)} vehicles...")
    
    service_types = ['General', 'Engine', 'Electrical', 'Brakes', 'AC/Cooling']
    problems = [
        'Regular maintenance and oil change',
        'Brake pad replacement',
        'Engine oil and filter change',
        'AC gas refill and service',
        'Battery replacement',
        'Tire rotation and alignment',
        'Spark plug replacement',
        'Coolant flush and refill'
    ]
    
    for vehicle in vehicles:
        vehicle_id = vehicle['id']
        
        # Add 2-3 historical services
        num_services = random.randint(2, 3)
        
        for i in range(num_services):
            # Service dates in the past
            days_ago = random.randint(30 + (i * 60), 180 + (i * 60))
            service_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            service_type = random.choice(service_types)
            problem = random.choice(problems)
            
            parts_cost = random.randint(500, 3000)
            labor_cost = random.randint(300, 1500)
            
            cursor.execute("""
                INSERT INTO services 
                (vehicle_id, date, problem, service_type, status, parts_cost, labor_cost, payment_status)
                VALUES (%s, %s, %s, %s, 'Completed', %s, %s, 'Paid')
            """, (vehicle_id, service_date, problem, service_type, parts_cost, labor_cost))
            
            print(f"  Added service for Vehicle {vehicle_id}: {problem} ({service_date})")
    
    conn.commit()
    conn.close()
    print("\n✅ Sample service history added!")

if __name__ == "__main__":
    print("=" * 60)
    print("Vehicle Health Analytics - Demo Data Population")
    print("=" * 60)
    print()
    
    try:
        populate_mileage_data()
        add_sample_service_history()
        
        print("\n" + "=" * 60)
        print("✨ Demo data setup complete!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Login to the customer dashboard")
        print("2. Navigate to 'Vehicle Health' tab")
        print("3. View AI-powered health analytics")
        print("4. Click 'View Detailed Analytics' for full insights")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("- PostgreSQL is running")
        print("- Database 'vehicle_service' exists")
        print("- Database credentials are correct")
