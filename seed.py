import psycopg2
from datetime import datetime, timedelta
import random

# Database Setup - matching app.py
DB_HOST = "localhost"
DB_NAME = "vehicle_service"
DB_USER = "postgres"
DB_PASS = "password"

def seed():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    # helper for unique data
    def get_suffix():
        return str(random.randint(1000, 9999))

    print("Seeding database...")

    # 1. Seed Technicians with Specializations
    technicians = [
        ('Mike Ross', 'mike@tech.com', '9000000001', 'mike123', 'Engine'),
        ('Sarah Jenkins', 'sarah@tech.com', '9000000002', 'sarah123', 'Electrical'),
        ('Tom Hardy', 'tom@tech.com', '9000000003', 'tom123', 'Brakes'),
        ('John Smith', 'john@tech.com', '9000000004', 'john123', 'General'),
        ('Emma Wilson', 'emma@tech.com', '9000000005', 'emma123', 'Transmission')
    ]
    
    tech_ids = []
    for name, email, phone, password, specialization in technicians:
        try:
            cursor.execute("INSERT INTO users (role, name, email, phone, password, specialization) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                           ('technician', name, email, phone, password, specialization))
            tech_ids.append(cursor.fetchone()[0])
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            tech_ids.append(cursor.fetchone()[0])
        except Exception as e:
            conn.rollback()
            print(f"Error seeding tech {name}: {e}")


    # 2. Seed Customers and Vehicles
    customers = [
        ('Alice Johnson', 'alice@example.com', '8000000001', 'alice123', [
            ('KA05MT1234', 'Toyota', 'Camry', 2021, 'ENG998877', 'CHS1122334455'),
            ('KA05MT5678', 'Honda', 'Civic', 2018, 'ENG554433', 'CHS5566778899')
        ]),
        ('Bob Wilson', 'bob@example.com', '8000000002', 'bob123', [
            ('KA01PK9999', 'Tesla', 'Model 3', 2023, 'ENG000001', 'CHS9988776655')
        ]),
        ('Carol White', 'carol@example.com', '8000000003', 'car123', [
            ('KA03XY4545', 'Ford', 'Mustang', 2015, 'ENG776655', 'CHS3344556677')
        ])
    ]

    vehicle_ids = []
    for name, email, phone, password, vehicles in customers:
        user_id = None
        try:
            cursor.execute("INSERT INTO users (role, name, email, phone, password) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                           ('customer', name, email, phone, password))
            user_id = cursor.fetchone()[0]
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_id = cursor.fetchone()[0]
        
        for reg, brand, model, year, eng, chs in vehicles:
            try:
                cursor.execute("INSERT INTO vehicles (owner_id, reg_no, brand, model, year, engine_no, chassis_no) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                               (user_id, reg, brand, model, year, eng, chs))
                vehicle_ids.append(cursor.fetchone()[0])
            except psycopg2.IntegrityError:
                conn.rollback()
                cursor.execute("SELECT id FROM vehicles WHERE reg_no = %s", (reg,))
                vehicle_ids.append(cursor.fetchone()[0])

    # 3. Seed Services
    problems = [
        "Oil change and general inspection",
        "Brake noise and shaky steering",
        "Engine overheating",
        "Battery replacement",
        "AC not cooling",
        "Tire rotation and alignment"
    ]
    
    statuses = ['Pending', 'Completed', 'Completed', 'Pending']
    
    # Past Services (Completed)
    TECH_COMMISSION_RATE = 0.20  # 20% of labor goes to technician
    for _ in range(5):
        vid = random.choice(vehicle_ids)
        tid = random.choice(tech_ids)
        date = (datetime.now() - timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d')
        prob = random.choice(problems)
        parts_cost = float(random.randint(500, 5000))
        labor_cost = float(random.randint(1000, 3000))
        wash_cost = float(random.choice([0, 100, 150, 200]))
        tech_commission = round(labor_cost * TECH_COMMISSION_RATE, 2)
        center_share = round((labor_cost - tech_commission) + parts_cost + wash_cost, 2)
        
        cursor.execute("""
            INSERT INTO services (vehicle_id, technician_id, date, problem, status, parts_details, parts_cost, labor_cost, wash_cost, tech_commission, center_share, payment_status, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (vid, tid, date, prob, 'Completed', 'Standard parts used', parts_cost, labor_cost, wash_cost, tech_commission, center_share, 'Paid', random.choice(['online', 'offline'])))

    # Active Services (Pending)
    for _ in range(3):
        vid = random.choice(vehicle_ids)
        date = datetime.now().strftime('%Y-%m-%d')
        prob = random.choice(problems)
        
        cursor.execute("""
            INSERT INTO services (vehicle_id, date, problem, status)
            VALUES (%s, %s, %s, %s)
        """, (vid, date, prob, 'Pending'))

    # 4. Seed Emergency Requests
    locations = ["Main Street, Downtown", "North Highway Exit 12", "South Mall Parking", "Airport Road"]
    emergency_probs = ["Flat tire", "Engine stall", "Locked out of car", "Smoke from hood"]
    
    cursor.execute("SELECT id FROM users WHERE role = 'customer'")
    cust_ids = [r[0] for r in cursor.fetchall()]
    
    for _ in range(3):
        uid = random.choice(cust_ids)
        loc = random.choice(locations)
        prob = random.choice(emergency_probs)
        cursor.execute("INSERT INTO emergency_requests (user_id, location, problem, status) VALUES (%s, %s, %s, 'Pending')",
                       (uid, loc, prob))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
