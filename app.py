from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, flash
import psycopg2
from psycopg2.extras import DictCursor
import os
from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

import csv
from io import StringIO
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_nextgen_secure_key_2026')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800 # 30 minutes
)

# Database Setup


# Database Setup
# Database Setup
DB_HOST = "localhost"
DB_NAME = "vehicle_service"
DB_USER = "postgres"
DB_PASS = "password" # Default password, change as needed

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=DictCursor
    )
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password TEXT NOT NULL,
        specialization TEXT
    )
    ''')
    
    # Add specialization column if it doesn't exist
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS specialization TEXT")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        owner_id INTEGER NOT NULL,
        reg_no TEXT UNIQUE NOT NULL,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        year INTEGER,
        engine_no TEXT,
        chassis_no TEXT,
        insurance_company TEXT,
        policy_no TEXT,
        policy_expiry TEXT,
        image_url TEXT,
        FOREIGN KEY (owner_id) REFERENCES users (id)
    )
    ''')
    
    # Add columns if they don't exist
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS image_url TEXT")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS insurance_company TEXT")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS policy_no TEXT")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS policy_expiry TEXT")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS current_mileage INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS last_mileage_update TEXT")
    
    # Services Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id SERIAL PRIMARY KEY,
        vehicle_id INTEGER NOT NULL,
        technician_id INTEGER,
        date TEXT NOT NULL,
        problem TEXT NOT NULL,
        request TEXT,
        status TEXT DEFAULT 'Pending',
        service_type TEXT,
        parts_details TEXT,
        parts_cost REAL DEFAULT 0,
        labor_cost REAL DEFAULT 0,
        wash_cost REAL DEFAULT 0,
        tech_commission REAL DEFAULT 0,
        center_share REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Unpaid',
        payment_method TEXT,
        rating INTEGER,
        feedback TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
        FOREIGN KEY (technician_id) REFERENCES users (id)
    )
    ''')
    
    # Add columns if they don't exist
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS wash_cost REAL DEFAULT 0")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS service_type TEXT")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS tech_commission REAL DEFAULT 0")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS center_share REAL DEFAULT 0")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS rating INTEGER")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS feedback TEXT")
    
    # Insurance Columns
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS is_insurance_claim BOOLEAN DEFAULT FALSE")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS claim_status TEXT") # Pending, Surveyor Assigned, Approved, Rejected, Settled
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS surveyor_name TEXT")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS damage_assessment TEXT")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS insurance_amount REAL DEFAULT 0")
    cursor.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS customer_deductible REAL DEFAULT 0")
    
    # Emergency Requests Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergency_requests (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        problem TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Inventory Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        brand TEXT,
        compatible_model TEXT,
        description TEXT,
        price REAL NOT NULL,
        purchase_price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        image_url TEXT,
        is_for_sale BOOLEAN DEFAULT FALSE
    )
    ''' )
    
    # Add purchase_price if it doesn't exist
    # Add purchase_price if it doesn't exist
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS purchase_price REAL DEFAULT 0")
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'General'")
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS is_for_sale BOOLEAN DEFAULT FALSE")
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS brand TEXT")
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS compatible_model TEXT")
    cursor.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS image_url TEXT")

    # Stock Purchases Table (to track expenses)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_purchases (
        id SERIAL PRIMARY KEY,
        inventory_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        purchase_price REAL NOT NULL,
        total_cost REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inventory_id) REFERENCES inventory (id)
    )
    ''')

    # Service Parts Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_parts (
        id SERIAL PRIMARY KEY,
        service_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        price_at_time REAL NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id),
        FOREIGN KEY (part_id) REFERENCES inventory (id)
    )
    ''')
    
    # Create Default Admin if not exists
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (role, name, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                       ('admin', 'Admin', 'admin@service.com', '0000000000', generate_password_hash('admin123')))
    
    # Seed Initial Inventory if empty
    cursor.execute("SELECT COUNT(*) as count FROM inventory")
    if cursor.fetchone()['count'] == 0:
        parts = [
            ('Engine Oil', 'Engine', 'Premium synthetic engine oil 5W-40', 1200.0, 800.0, 50, 'https://images.unsplash.com/photo-1635816823861-512803bba221?q=80&w=800'),
            ('Brake Pads', 'Braking', 'Semi-metallic front brake pads', 850.0, 500.0, 30, 'https://images.unsplash.com/photo-1486006396193-471e6158ecfb?q=80&w=800'),
            ('Air Filter', 'Filters', 'High-flow air filter', 450.0, 300.0, 40, 'https://images.unsplash.com/photo-1621259182978-fbf93132d53d?q=80&w=800'),
            ('Oil Filter', 'Filters', 'Spin-on oil filter', 300.0, 150.0, 100, 'https://images.unsplash.com/photo-1598460671400-9883584852c0?q=80&w=800'),
            ('Spark Plug', 'Engine', 'Iridium spark plug', 350.0, 200.0, 60, 'https://images.unsplash.com/photo-1632733711679-52923aa9e170?q=80&w=800'),
            ('Battery', 'Electrical', '12V 35Ah Lead Acid Battery', 3500.0, 2500.0, 10, 'https://images.unsplash.com/photo-1620939511593-29937fd09903?q=80&w=800'),
            ('Coolant', 'Fluids', 'Engine coolant 1L', 250.0, 150.0, 25, 'https://images.unsplash.com/photo-1621259182046-2b4751421711?q=80&w=800'),
            ('Wiper Blade', 'Accessories', '20-inch wiper blade', 200.0, 100.0, 40, 'https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?q=80&w=800')
        ]
        cursor.executemany("INSERT INTO inventory (name, category, description, price, purchase_price, stock, image_url, is_for_sale) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)", parts)
        
        # Record initial stock as purchases
        cursor.execute("SELECT id, purchase_price, stock FROM inventory")
        for inv in cursor.fetchall():
            cursor.execute("INSERT INTO stock_purchases (inventory_id, quantity, purchase_price, total_cost) VALUES (%s, %s, %s, %s)",
                           (inv['id'], inv['stock'], inv['purchase_price'], inv['stock'] * inv['purchase_price']))

    # Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # Service Bundles Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bundles (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        labor_cost REAL DEFAULT 0,
        discount_rate REAL DEFAULT 0
    )
    ''')
    
    # Bundle Items Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bundle_items (
        id SERIAL PRIMARY KEY,
        bundle_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (bundle_id) REFERENCES bundles (id),
        FOREIGN KEY (part_id) REFERENCES inventory (id)
    )
    ''')
    
    # Default Slots
    cursor.execute("SELECT * FROM settings WHERE key = 'daily_capacity'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s)", ('daily_capacity', '5'))
        
    cursor.execute("SELECT * FROM settings WHERE key = 'tech_commission_rate'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s)", ('tech_commission_rate', '20')) # 20% commission

    cursor.execute("SELECT * FROM settings WHERE key = 'washing_capacity'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s)", ('washing_capacity', '3'))

    # Orders Table (Direct Sales)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        location TEXT NOT NULL,
        part_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (part_id) REFERENCES inventory (id)
    )
    ''')

    # Secure Migration: Hash any plain text passwords
    cursor.execute("SELECT id, password FROM users")
    users = cursor.fetchall()
    for user in users:
        stored_pw = user['password']
        if not (stored_pw.startswith('pbkdf2:sha256:') or stored_pw.startswith('scrypt:')):
            hashed = generate_password_hash(stored_pw)
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user['id']))
    
    # Data Repair: Recalculate tech_commission & center_share for services where both are 0
    # (covers seeded/legacy records that were inserted without commission data)
    cursor.execute("SELECT value FROM settings WHERE key = 'tech_commission_rate'")
    rate_row = cursor.fetchone()
    commission_rate = float(rate_row['value']) / 100.0 if rate_row else 0.20

    cursor.execute("""
        UPDATE services
        SET 
            tech_commission = ROUND((labor_cost * %s)::numeric, 2),
            center_share    = ROUND(((labor_cost - labor_cost * %s) + COALESCE(parts_cost, 0) + COALESCE(wash_cost, 0))::numeric, 2)
        WHERE (tech_commission = 0 AND center_share = 0)
          AND (labor_cost > 0 OR parts_cost > 0)
    """, (commission_rate, commission_rate))

    conn.commit()
    conn.close()

init_db()

def auto_assign_technician(service_type=None):
    """
    Automatically assigns the best technician based on:
    1. Matching specialization (if service_type is provided)
    2. Least active services (load balancing)
    
    Returns: technician_id or None if no technician available
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query to find technicians with their active service count
    if service_type:
        # Find technicians with matching specialization
        query = """
            SELECT u.id, u.name, u.specialization,
                   COUNT(s.id) as active_services
            FROM users u
            LEFT JOIN services s ON u.id = s.technician_id 
                AND s.status NOT IN ('Completed', 'Ready for Wash', 'Washing')
            WHERE u.role = 'technician' 
                AND (u.specialization = %s OR u.specialization IS NULL OR u.specialization = 'General')
            GROUP BY u.id, u.name, u.specialization
            ORDER BY active_services ASC, u.id ASC
            LIMIT 1
        """
        cursor.execute(query, (service_type,))
    else:
        # No service type specified, just find least loaded technician
        query = """
            SELECT u.id, u.name, u.specialization,
                   COUNT(s.id) as active_services
            FROM users u
            LEFT JOIN services s ON u.id = s.technician_id 
                AND s.status NOT IN ('Completed', 'Ready for Wash', 'Washing')
            WHERE u.role = 'technician'
            GROUP BY u.id, u.name, u.specialization
            ORDER BY active_services ASC, u.id ASC
            LIMIT 1
        """
        cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result['id']
    return None


def calculate_vehicle_health_score(vehicle_id):
    """
    AI-Based Vehicle Health Score Calculator
    
    Analyzes:
    - Mileage patterns
    - Service history frequency
    - Repair frequency and severity
    - Time since last service
    
    Returns: Dictionary with health score (0-100) and detailed insights
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get vehicle details
    cursor.execute("""
        SELECT v.*, u.name as owner_name
        FROM vehicles v
        JOIN users u ON v.owner_id = u.id
        WHERE v.id = %s
    """, (vehicle_id,))
    vehicle = cursor.fetchone()
    
    if not vehicle:
        conn.close()
        return None
    
    # Get service history
    cursor.execute("""
        SELECT * FROM services 
        WHERE vehicle_id = %s 
        ORDER BY date DESC
    """, (vehicle_id,))
    services = cursor.fetchall()
    
    # Initialize scoring components
    score = 100
    insights = []
    recommendations = []
    health_status = "Excellent"
    
    # 1. MILEAGE ANALYSIS (20 points max deduction)
    current_mileage = vehicle.get('current_mileage', 0) or 0
    vehicle_age = datetime.now().year - (vehicle.get('year') or datetime.now().year)
    
    if vehicle_age > 0:
        avg_yearly_mileage = current_mileage / vehicle_age
        if avg_yearly_mileage > 20000:
            score -= 15
            insights.append(f"⚠️ High annual mileage: {int(avg_yearly_mileage):,} km/year")
            recommendations.append("Consider more frequent oil changes and brake inspections")
        elif avg_yearly_mileage > 15000:
            score -= 8
            insights.append(f"📊 Above average mileage: {int(avg_yearly_mileage):,} km/year")
        else:
            insights.append(f"✅ Normal mileage: {int(avg_yearly_mileage):,} km/year")
    
    # 2. SERVICE FREQUENCY ANALYSIS (25 points max deduction)
    if len(services) > 0:
        completed_services = [s for s in services if s['status'] == 'Completed']
        
        if len(completed_services) > 0:
            # Check last service date
            last_service = completed_services[0]
            last_service_date = datetime.strptime(last_service['date'], '%Y-%m-%d')
            days_since_service = (datetime.now() - last_service_date).days
            
            if days_since_service > 180:  # 6 months
                score -= 20
                insights.append(f"🔴 Service overdue by {days_since_service - 180} days")
                recommendations.append("⚡ URGENT: Schedule immediate service inspection")
            elif days_since_service > 150:
                score -= 10
                insights.append(f"⚠️ Service due soon ({180 - days_since_service} days remaining)")
                recommendations.append("Schedule service within 2 weeks")
            else:
                insights.append(f"✅ Last serviced {days_since_service} days ago")
            
            # Calculate service frequency
            if len(completed_services) >= 2:
                service_dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in completed_services[:5]]
                intervals = [(service_dates[i] - service_dates[i+1]).days for i in range(len(service_dates)-1)]
                avg_interval = sum(intervals) / len(intervals) if intervals else 180
                
                if avg_interval > 210:
                    score -= 5
                    insights.append("⚠️ Irregular service intervals detected")
                    recommendations.append("Maintain regular 6-month service schedule")
        else:
            score -= 25
            insights.append("🔴 No completed services found")
            recommendations.append("⚡ CRITICAL: Schedule comprehensive vehicle inspection")
    else:
        score -= 25
        insights.append("🔴 No service history available")
        recommendations.append("⚡ CRITICAL: Complete initial vehicle assessment")
    
    # 3. REPAIR FREQUENCY & SEVERITY (30 points max deduction)
    total_services = len(services)
    repair_keywords = ['repair', 'replace', 'fix', 'broken', 'damage', 'fault', 'issue', 'problem']
    
    repair_count = 0
    major_repairs = 0
    total_repair_cost = 0
    
    for service in services:
        problem_text = (service.get('problem', '') or '').lower()
        parts_details = (service.get('parts_details', '') or '').lower()
        
        is_repair = any(keyword in problem_text or keyword in parts_details for keyword in repair_keywords)
        
        if is_repair:
            repair_count += 1
            service_cost = (service.get('parts_cost', 0) or 0) + (service.get('labor_cost', 0) or 0)
            total_repair_cost += service_cost
            
            if service_cost > 5000:
                major_repairs += 1
    
    if total_services > 0:
        repair_ratio = repair_count / total_services
        
        if repair_ratio > 0.6:
            score -= 25
            insights.append(f"🔴 High repair frequency: {repair_count}/{total_services} services")
            recommendations.append("⚡ Consider comprehensive diagnostic check")
        elif repair_ratio > 0.4:
            score -= 15
            insights.append(f"⚠️ Moderate repair frequency: {repair_count}/{total_services} services")
            recommendations.append("Monitor vehicle closely for recurring issues")
        else:
            insights.append(f"✅ Low repair frequency: {repair_count}/{total_services} services")
        
        if major_repairs > 2:
            score -= 10
            insights.append(f"⚠️ {major_repairs} major repairs detected (₹5000+)")
            recommendations.append("Review vehicle reliability - consider upgrade if issues persist")
    
    # 4. COST ANALYSIS (15 points max deduction)
    if total_services > 0:
        avg_service_cost = total_repair_cost / total_services if total_services > 0 else 0
        
        if avg_service_cost > 8000:
            score -= 15
            insights.append(f"💰 High average service cost: ₹{int(avg_service_cost):,}")
            recommendations.append("Budget for potential major maintenance")
        elif avg_service_cost > 5000:
            score -= 8
            insights.append(f"💰 Above average service cost: ₹{int(avg_service_cost):,}")
        else:
            insights.append(f"✅ Reasonable service cost: ₹{int(avg_service_cost):,}")
    
    # 5. VEHICLE AGE FACTOR (10 points max deduction)
    if vehicle_age > 10:
        score -= 10
        insights.append(f"📅 Older vehicle: {vehicle_age} years")
        recommendations.append("Consider preventive maintenance for aging components")
    elif vehicle_age > 7:
        score -= 5
        insights.append(f"📅 Mature vehicle: {vehicle_age} years")
        recommendations.append("Monitor wear-prone parts closely")
    else:
        insights.append(f"✅ Vehicle age: {vehicle_age} years")
    
    # Ensure score stays within 0-100
    score = max(0, min(100, score))
    
    # Determine health status and color
    if score >= 85:
        health_status = "Excellent"
        status_color = "#10b981"  # Green
        status_icon = "🟢"
    elif score >= 70:
        health_status = "Good"
        status_color = "#3b82f6"  # Blue
        status_icon = "🔵"
    elif score >= 50:
        health_status = "Fair"
        status_color = "#f59e0b"  # Orange
        status_icon = "🟠"
    else:
        health_status = "Poor"
        status_color = "#ef4444"  # Red
        status_icon = "🔴"
    
    # PREDICTIVE MAINTENANCE SCHEDULE
    next_service_date = None
    if len(services) > 0 and services[0]['status'] == 'Completed':
        last_date = datetime.strptime(services[0]['date'], '%Y-%m-%d')
        # Calculate 6 months ahead
        month = last_date.month + 6
        year = last_date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(last_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        next_service_date = datetime(year, month, day).strftime('%Y-%m-%d')
    else:
        next_service_date = datetime.now().strftime('%Y-%m-%d')
    
    # Suggested maintenance based on mileage
    maintenance_suggestions = []
    if current_mileage > 0:
        if current_mileage >= 100000:
            maintenance_suggestions.append("🔧 Major service recommended (100k+ km)")
            maintenance_suggestions.append("Check timing belt/chain, suspension, transmission")
        elif current_mileage >= 50000:
            maintenance_suggestions.append("🔧 Intermediate service recommended (50k+ km)")
            maintenance_suggestions.append("Inspect brake system, coolant, spark plugs")
        elif current_mileage >= 20000:
            maintenance_suggestions.append("🔧 Standard service recommended")
            maintenance_suggestions.append("Oil change, filter replacement, tire rotation")
        else:
            maintenance_suggestions.append("🔧 Basic service recommended")
            maintenance_suggestions.append("Oil change and basic inspection")
    
    conn.close()
    
    return {
        'score': round(score, 1),
        'status': health_status,
        'status_color': status_color,
        'status_icon': status_icon,
        'insights': insights,
        'recommendations': recommendations,
        'maintenance_suggestions': maintenance_suggestions,
        'next_service_date': next_service_date,
        'total_services': total_services,
        'repair_count': repair_count,
        'current_mileage': current_mileage,
        'vehicle_age': vehicle_age,
        'avg_service_cost': round(total_repair_cost / total_services, 2) if total_services > 0 else 0
    }


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE is_for_sale = TRUE AND stock > 0 ORDER BY id DESC LIMIT 4")
    parts = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE is_for_sale = TRUE AND stock > 0")
    total_parts = cursor.fetchone()[0]
    
    conn.close()
    return render_template('index.html', parts=parts, total_parts=total_parts)

@app.route('/shop')
def shop():
    search = request.args.get('search', '')
    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    
    query = "SELECT * FROM inventory WHERE is_for_sale = TRUE AND stock > 0"
    params = []
    
    if search:
        query += " AND (name ILIKE %s OR description ILIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
        
    if brand:
        query += " AND brand = %s"
        params.append(brand)
        
    if model:
        query += " AND compatible_model = %s"
        params.append(model)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    parts = cursor.fetchall()
    
    # Get filters
    cursor.execute("SELECT DISTINCT brand FROM inventory WHERE is_for_sale = TRUE AND brand IS NOT NULL")
    brands = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT compatible_model FROM inventory WHERE is_for_sale = TRUE AND compatible_model IS NOT NULL")
    models = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    return render_template('shop.html', parts=parts, brands=brands, models=models)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if role == 'customer':
            cursor.execute("SELECT * FROM users WHERE (email = %s OR phone = %s) AND role = %s", (identifier, identifier, role))
        else:
            if identifier and identifier.isdigit():
                cursor.execute("SELECT * FROM users WHERE (id = %s OR email = %s) AND role = %s", (identifier, identifier, role))
            else:
                cursor.execute("SELECT * FROM users WHERE email = %s AND role = %s", (identifier, role))
            
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = user.get('email', '')
            session['phone'] = user.get('phone', '')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'technician':
                return redirect(url_for('technician_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            return "Invalid Credentials", 401
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        reg_no = request.form.get('reg_no')
        phone = request.form.get('phone')
        email = request.form.get('email')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        engine_no = request.form.get('engine_no')
        chassis_no = request.form.get('chassis_no')
        password = request.form.get('password')
        
        brand_images = {
            'Maruti Suzuki': 'https://images.unsplash.com/photo-1549490349-8643362247b5?q=80&w=1200',
            'Hyundai': 'https://images.unsplash.com/photo-1583121274602-3e2820c69888?q=80&w=1200',
            'Tata Motors': 'https://images.unsplash.com/photo-1603386329225-868f9b1ee6c9?q=80&w=1200',
            'Mahindra': 'https://images.unsplash.com/photo-1620608146313-2df67cc85766?q=80&w=1200',
            'Toyota': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?q=80&w=1200',
            'Honda': 'https://images.unsplash.com/photo-1616455572844-825649a67b47?q=80&w=1200',
            'BMW': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?q=80&w=1200',
            'Skoda': 'https://images.unsplash.com/photo-1594541818129-417d4722a84a?q=80&w=1200',
            'Kia': 'https://images.unsplash.com/photo-1632243193044-8e979827d52b?q=80&w=1200',
            'Volkswagen': 'https://images.unsplash.com/photo-1617469767053-d3b508a0d182?q=80&w=1200',
            'Renault': 'https://images.unsplash.com/photo-1613134268686-235b2e5cc8f2?q=80&w=1200',
            'Audi': 'https://images.unsplash.com/photo-1606152421631-f22758296719?q=80&w=1200',
            'Mercedes-Benz': 'https://images.unsplash.com/photo-1618843479313-4b88afaa5e6c?q=80&w=1200'
        }
        image_url = brand_images.get(brand, 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=800')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (role, name, email, phone, password) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                           ('customer', name, email, phone, hashed_pw))
            user_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO vehicles (owner_id, reg_no, brand, model, year, engine_no, chassis_no, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, reg_no, brand, model, year, engine_no, chassis_no, image_url))
            conn.commit()
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            return f"Error: {e}", 400
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate Reminders
    cursor.execute("SELECT * FROM vehicles WHERE owner_id = %s", (session['user_id'],))
    my_vehicles = cursor.fetchall()
    reminders = []
    
    for v in my_vehicles:
        cursor.execute("""
            SELECT date FROM services 
            WHERE vehicle_id = %s AND status = 'Completed' 
            ORDER BY date DESC LIMIT 1
        """, (v['id'],))
        last_service = cursor.fetchone()
        
        if last_service:
            last_date = datetime.strptime(last_service['date'], '%Y-%m-%d')
            # Robust 6-month addition
            month = last_date.month + 6
            year = last_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(last_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            due_date = datetime(year, month, day)
            
            days_left = (due_date - datetime.now()).days
            if days_left <= 15:
                reminders.append({
                    'reg_no': v['reg_no'],
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'is_overdue': days_left < 0
                })

    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.model, vehicles.image_url, users.name as tech_name 
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        LEFT JOIN users ON services.technician_id = users.id 
        WHERE vehicles.owner_id = %s 
        ORDER BY services.id DESC
    """, (session['user_id'],))
    history = cursor.fetchall()
    
    cursor.execute("SELECT * FROM vehicles WHERE owner_id = %s", (session['user_id'],))
    vehicles = cursor.fetchall()
    conn.close()
    
    return render_template('customer_dashboard.html', history=history, vehicles=vehicles, reminders=reminders)

@app.route('/export_history')
def export_history():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if session['role'] == 'admin':
        cursor.execute("""
            SELECT s.date, v.reg_no, v.brand, v.model, u.name as owner, s.problem, s.status, s.parts_cost + s.labor_cost as total
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.id
            JOIN users u ON v.owner_id = u.id
        """)
    else:
        cursor.execute("""
            SELECT s.date, v.reg_no, v.brand, v.model, s.problem, s.status, s.parts_cost + s.labor_cost as total
            FROM services s
            JOIN vehicles v ON s.vehicle_id = v.id
            WHERE v.owner_id = %s
        """, (session['user_id'],))
        
    rows = cursor.fetchall()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    
    if session['role'] == 'admin':
        cw.writerow(['Date', 'Vehicle No', 'Brand', 'Model', 'Owner', 'Problem', 'Status', 'Total Amount (₹)'])
    else:
        cw.writerow(['Date', 'Vehicle No', 'Brand', 'Model', 'Problem', 'Status', 'Total Amount (₹)'])
        
    for row in rows:
        cw.writerow(list(row))
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=service_history_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

@app.route('/book_service', methods=['POST'])
def book_service():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    vehicle_id = request.form.get('vehicle_id')
    date = request.form.get('date')
    problem = request.form.get('problem')
    request_text = request.form.get('request')
    service_type = request.form.get('service_type', 'General')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    


    # Auto-assign technician based on service type and load
    assigned_tech_id = auto_assign_technician(service_type)
    
    is_insurance = request.form.get('is_insurance') == 'on'
    claim_status = 'Pending' if is_insurance else None
    
    cursor.execute("""
        INSERT INTO services (vehicle_id, date, problem, request, service_type, technician_id, status, is_insurance_claim, claim_status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (vehicle_id, date, problem, request_text, service_type, assigned_tech_id, 'Assigned' if assigned_tech_id else 'Pending', is_insurance, claim_status))
    conn.commit()
    conn.close()
    return redirect(url_for('customer_dashboard'))

@app.route('/update_insurance', methods=['POST'])
def update_insurance():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    vehicle_id = request.form.get('vehicle_id')
    company = request.form.get('insurance_company')
    policy_no = request.form.get('policy_no')
    expiry = request.form.get('policy_expiry')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vehicles 
        SET insurance_company = %s, policy_no = %s, policy_expiry = %s 
        WHERE id = %s AND owner_id = %s
    """, (company, policy_no, expiry, vehicle_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('customer_dashboard'))

@app.route('/update_claim', methods=['POST'])
def update_claim():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    service_id = request.form.get('service_id')
    status = request.form.get('claim_status')
    surveyor = request.form.get('surveyor_name')
    ins_amount = float(request.form.get('insurance_amount') or 0)
    deductible = float(request.form.get('customer_deductible') or 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE services 
        SET claim_status = %s, surveyor_name = %s, insurance_amount = %s, customer_deductible = %s 
        WHERE id = %s
    """, (status, surveyor, ins_amount, deductible, service_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/emergency', methods=['POST'])
def emergency():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    location = request.form.get('location')
    problem = request.form.get('problem')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO emergency_requests (user_id, location, problem) VALUES (%s, %s, %s)",
                   (session['user_id'], location, problem))
    conn.commit()
    conn.close()
    return redirect(url_for('customer_dashboard'))

@app.route('/technician_dashboard')
def technician_dashboard():
    if 'user_id' not in session or session['role'] != 'technician':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.model, vehicles.image_url, users.name as owner_name, users.phone as owner_phone 
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        WHERE services.status NOT IN ('Completed', 'Ready for Wash', 'Washing')
        AND services.technician_id = %s
        ORDER BY services.date ASC
    """, (session['user_id'],))
    tasks = cursor.fetchall()

    # Calculate revenue for this technician
    cursor.execute("""
        SELECT SUM(tech_commission) as total_earnings,
               SUM(parts_cost + labor_cost) as total_generated
        FROM services 
        WHERE technician_id = %s AND status = 'Completed'
    """, (session['user_id'],))
    rec = cursor.fetchone()
    total_earnings = rec['total_earnings'] or 0
    total_generated = rec['total_generated'] or 0

    # Get completed services count
    cursor.execute("SELECT COUNT(*) as count FROM services WHERE technician_id = %s AND status = 'Completed'", (session['user_id'],))
    completed_count = cursor.fetchone()['count']

    # Get average rating
    cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(rating) as rating_count FROM services WHERE technician_id = %s AND rating IS NOT NULL", (session['user_id'],))
    rating_data = cursor.fetchone()
    avg_rating = round(float(rating_data['avg_rating'] or 0), 1)
    rating_count = rating_data['rating_count']

    # Get latest feedback
    cursor.execute("""
        SELECT s.feedback, s.rating, v.reg_no, u.name as owner_name, s.date
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.id
        JOIN users u ON v.owner_id = u.id
        WHERE s.technician_id = %s AND s.rating IS NOT NULL
        ORDER BY s.id DESC LIMIT 5
    """, (session['user_id'],))
    feedbacks = cursor.fetchall()

    cursor.execute("SELECT * FROM inventory WHERE stock > 0")
    inventory = cursor.fetchall()
    cursor.execute("SELECT value FROM settings WHERE key = 'tech_commission_rate'")
    tech_commission_rate = cursor.fetchone()['value']
    conn.close()
    
    statuses = ["Pending", "Assigned", "Inspecting", "In Service", "Quality Check"]
    return render_template('technician_dashboard.html', 
                           tasks=tasks, 
                           inventory=inventory, 
                           statuses=statuses, 
                           total_revenue=total_earnings,
                           total_generated=total_generated,
                           completed_count=completed_count,
                           tech_commission_rate=tech_commission_rate,
                           avg_rating=avg_rating,
                           rating_count=rating_count,
                           feedbacks=feedbacks)

@app.route('/update_status', methods=['POST'])
def update_status():
    if 'user_id' not in session or session['role'] != 'technician': return redirect(url_for('login'))
    
    service_id = request.form.get('service_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET status = %s, technician_id = %s WHERE id = %s", (new_status, session['user_id'], service_id))
    conn.commit()
    conn.close()
    flash('Status Updated Successfully! ✅')
    return redirect(url_for('technician_dashboard'))

@app.route('/update_service', methods=['POST'])
def update_service():
    if 'user_id' not in session or session['role'] != 'technician': return redirect(url_for('login'))
    
    service_id = request.form.get('service_id')
    parts_details = request.form.get('parts_details')
    misc_cost = float(request.form.get('misc_cost') or 0)
    hours = float(request.form.get('hours') or 0)
    wash_cost = float(request.form.get('wash_cost') or 0)
    labor_rate = 500
    labor_cost = hours * labor_rate
    
    part_ids = request.form.getlist('part_ids')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total_parts_cost = misc_cost
    inventory_details = ""
    
    for p_id in part_ids:
        raw_qty = request.form.get(f'qty_{p_id}')
        qty = int(raw_qty) if raw_qty and raw_qty.strip() != "" else 0
        
        if qty > 0:
            cursor.execute("SELECT * FROM inventory WHERE id = %s", (p_id,))
            part = cursor.fetchone()
            if part:
                cost = part['price'] * qty
                total_parts_cost += cost
                cursor.execute("INSERT INTO service_parts (service_id, part_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                               (service_id, p_id, qty, part['price']))
                cursor.execute("UPDATE inventory SET stock = stock - %s WHERE id = %s", (qty, p_id))
                inventory_details += f"\n• {part['name']} (x{qty})"

    # Calculate Revenue Split
    cursor.execute("SELECT value FROM settings WHERE key = 'tech_commission_rate'")
    rate = int(cursor.fetchone()['value']) / 100
    tech_commission = labor_cost * rate
    # Center share now includes wash_cost
    center_share = (labor_cost - tech_commission) + total_parts_cost + wash_cost

    final_parts_details = parts_details + inventory_details
    
    damage_assessment = request.form.get('damage_assessment')
    
    cursor.execute("""
        UPDATE services 
        SET parts_details = %s, parts_cost = %s, labor_cost = %s, wash_cost = %s,
            tech_commission = %s, center_share = %s, 
            technician_id = %s, status = 'Completed',
            damage_assessment = %s
        WHERE id = %s
    """, (final_parts_details, total_parts_cost, labor_cost, wash_cost, tech_commission, center_share, session['user_id'], damage_assessment, service_id))
    conn.commit()
    conn.close()
    flash('Job Completed and Bill Generated! ✅')
    return redirect(url_for('technician_dashboard'))

@app.route('/move_to_wash', methods=['POST'])
def move_to_wash():
    if 'user_id' not in session or session['role'] != 'technician': return redirect(url_for('login'))
    service_id = request.form.get('service_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET status = 'Ready for Wash' WHERE id = %s", (service_id,))
    conn.commit()
    conn.close()
    flash('Vehicle moved to Washing Bay! ✅')
    return redirect(url_for('technician_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'customer'")
    customers = cursor.fetchall()



    cursor.execute("SELECT value FROM settings WHERE key = 'tech_commission_rate'")
    tech_commission_rate = cursor.fetchone()['value'] or '20'
    
    cursor.execute("""
        SELECT u.*, 
               COALESCE(SUM(CASE WHEN s.status = 'Completed' THEN s.parts_cost + s.labor_cost ELSE 0 END), 0) as total_revenue,
               COUNT(CASE WHEN s.status = 'Completed' THEN 1 END) as completed_jobs,
               COUNT(CASE WHEN s.status NOT IN ('Completed', 'Ready for Wash', 'Washing') THEN 1 END) as active_services
        FROM users u
        LEFT JOIN services s ON u.id = s.technician_id
        WHERE u.role = 'technician'
        GROUP BY u.id
    """)
    technicians = cursor.fetchall()
    
    cursor.execute("SELECT emergency_requests.*, users.name FROM emergency_requests JOIN users ON emergency_requests.user_id = users.id")
    emergencies = cursor.fetchall()
    
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.image_url, users.name as owner_name, users.phone as owner_phone, users.email as owner_email
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        WHERE payment_status = 'Unpaid' AND payment_method = 'offline'
    """)
    offline_requests = cursor.fetchall()
    
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.image_url, users.name as owner_name, tech.name as tech_name
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        LEFT JOIN users as tech ON services.technician_id = tech.id
        WHERE rating IS NOT NULL
        ORDER BY id DESC
    """)
    feedbacks = cursor.fetchall()
    
    cursor.execute("""
        SELECT SUM(CASE 
            WHEN is_insurance_claim = TRUE THEN COALESCE(insurance_amount, 0) + COALESCE(customer_deductible, 0)
            ELSE COALESCE(parts_cost, 0) + COALESCE(labor_cost, 0) + COALESCE(wash_cost, 0)
        END) as service_revenue 
        FROM services 
        WHERE payment_status = 'Paid'
    """)
    service_revenue = cursor.fetchone()['service_revenue'] or 0
    
    cursor.execute("SELECT SUM(total_amount) as sales_revenue FROM orders WHERE status != 'Cancelled'")
    sales_revenue = cursor.fetchone()['sales_revenue'] or 0
    
    gross_revenue = service_revenue + sales_revenue
    
    cursor.execute("SELECT SUM(total_cost) as total_expenses FROM stock_purchases")
    total_expenses = cursor.fetchone()['total_expenses'] or 0
    
    net_revenue = gross_revenue - total_expenses
    
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, users.name as owner_name, 
               users.phone as owner_phone, users.email as owner_email,
               tech.name as tech_name, tech.phone as tech_phone, tech.email as tech_email,
               (CASE 
                    WHEN is_insurance_claim = TRUE THEN COALESCE(services.insurance_amount, 0) + COALESCE(services.customer_deductible, 0)
                    ELSE COALESCE(services.parts_cost, 0) + COALESCE(services.labor_cost, 0) + COALESCE(services.wash_cost, 0)
                END) as row_total
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        LEFT JOIN users as tech ON services.technician_id = tech.id
        WHERE services.payment_status = 'Paid'
        ORDER BY services.id DESC
    """)
    completed_services = cursor.fetchall()
    
    cursor.execute("SELECT * FROM inventory ORDER BY category, name")
    all_inventory = cursor.fetchall()
    
    inventory_items = {}
    for item in all_inventory:
        cat = item['category']
        if cat not in inventory_items:
            inventory_items[cat] = []
        inventory_items[cat].append(item)
    
    # Calculate Overdue Services
    cursor.execute("SELECT id, reg_no, owner_id FROM vehicles")
    all_vehicles = cursor.fetchall()
    overdue_alerts = []
    for v in all_vehicles:
        cursor.execute("SELECT date FROM services WHERE vehicle_id = %s AND status = 'Completed' ORDER BY date DESC LIMIT 1", (v['id'],))
        last_s = cursor.fetchone()
        if last_s:
            l_date = datetime.strptime(last_s['date'], '%Y-%m-%d')
            # Robust 6-month addition
            _m = l_date.month + 6
            _y = l_date.year + (_m - 1) // 12
            _m = (_m - 1) % 12 + 1
            _dim = [31, 29 if _y % 4 == 0 and (_y % 100 != 0 or _y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            _d = min(l_date.day, _dim[_m-1])
            d_date = datetime(_y, _m, _d)
            if d_date < datetime.now():
                cursor.execute("SELECT name, phone FROM users WHERE id = %s", (v['owner_id'],))
                owner = cursor.fetchone()
                overdue_alerts.append({
                    'reg_no': v['reg_no'],
                    'owner': owner['name'],
                    'phone': owner['phone'],
                    'due_since': d_date.strftime('%Y-%m-%d')
                })

    # Financial Split Calculation (only for Paid services to match revenue table)
    cursor.execute("SELECT SUM(tech_commission) as total_payouts, SUM(center_share) as total_shares FROM services WHERE payment_status = 'Paid'")
    payout_data = cursor.fetchone()
    total_tech_payouts = payout_data['total_payouts'] or 0
    total_center_shares = payout_data['total_shares'] or 0

    # Washing Queue
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.image_url, users.name as owner_name 
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        WHERE services.status IN ('Ready for Wash', 'Washing')
    """)
    wash_queue = cursor.fetchall()

    # Service Queue (New Bookings & In-Progress)
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, vehicles.brand, vehicles.image_url, users.name as owner_name, users.phone as owner_phone
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        WHERE services.status IN ('Pending', 'Scheduled')
        ORDER BY services.date ASC
    """)
    service_queue = cursor.fetchall()
    
    # Fetch Orders
    cursor.execute("""
        SELECT orders.*, inventory.name as part_name, inventory.brand
        FROM orders
        JOIN inventory ON orders.part_id = inventory.id
        ORDER BY orders.date DESC
    """)
    orders = cursor.fetchall()

    # Fetch Insurance Claims
    cursor.execute("""
        SELECT services.*, vehicles.reg_no, users.name as owner_name, users.phone as owner_phone, users.email as owner_email,
               vehicles.insurance_company, vehicles.policy_no, tech.name as tech_name
        FROM services 
        JOIN vehicles ON services.vehicle_id = vehicles.id 
        JOIN users ON vehicles.owner_id = users.id 
        LEFT JOIN users as tech ON services.technician_id = tech.id
        WHERE is_insurance_claim = TRUE
        ORDER BY services.id DESC
    """)
    insurance_claims = cursor.fetchall()

    # --- Enhanced Revenue Analytics for Chart ---
    cursor.execute("""
        WITH daily_services AS (
            SELECT 
                date, 
                SUM(CASE WHEN is_insurance_claim = TRUE THEN 0 ELSE labor_cost END) as labor,
                SUM(CASE 
                    WHEN is_insurance_claim = TRUE THEN COALESCE(insurance_amount, 0) + COALESCE(customer_deductible, 0) 
                    ELSE COALESCE(parts_cost, 0) 
                END) as parts,
                SUM(CASE WHEN is_insurance_claim = TRUE THEN 0 ELSE wash_cost END) as wash
            FROM services WHERE payment_status = 'Paid'
            GROUP BY date
        ),
        daily_orders AS (
            SELECT CAST(date AS DATE) as date, SUM(total_amount) as amount
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY CAST(date AS DATE)
        )
        SELECT 
            COALESCE(s.date, CAST(o.date AS TEXT)) as rev_date,
            COALESCE(s.labor, 0) as labor,
            COALESCE(s.parts, 0) as service_parts,
            COALESCE(s.wash, 0) as wash,
            COALESCE(o.amount, 0) as direct_sales,
            (COALESCE(s.labor, 0) + COALESCE(s.parts, 0) + COALESCE(s.wash, 0) + COALESCE(o.amount, 0)) as total
        FROM daily_services s
        FULL OUTER JOIN daily_orders o ON s.date = CAST(o.date AS TEXT)
        ORDER BY rev_date DESC 
        LIMIT 30
    """)
    analytics = cursor.fetchall()
    
    # Pack data for frontend (reversed for chronological order)
    chart_data = {
        'labels': [r['rev_date'] for r in reversed(analytics)],
        'total': [float(r['total']) for r in reversed(analytics)],
        'labor': [float(r['labor']) for r in reversed(analytics)],
        'parts': [float(r['service_parts'] + r['direct_sales']) for r in reversed(analytics)],
        'wash': [float(r['wash']) for r in reversed(analytics)]
    }

    conn.close()
    return render_template('admin_dashboard.html', 
                           customers=customers, 
                           technicians=technicians, 
                           emergencies=emergencies, 
                           offline_requests=offline_requests, 
                           feedbacks=feedbacks,

                           gross_revenue=gross_revenue,
                           total_expenses=total_expenses,
                           total_revenue=net_revenue,
                           total_tech_payouts=total_tech_payouts,
                           total_center_shares=total_center_shares,
                           wash_queue=wash_queue,
                           completed_services=completed_services,
                           inventory_items=inventory_items,
                           overdue_alerts=overdue_alerts,

                           orders=orders,
                           analytics_json=chart_data,
                           insurance_claims=insurance_claims,
                           tech_commission_rate=tech_commission_rate,
                           service_queue=service_queue)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    service_id = request.form.get('service_id')
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE services 
        SET rating = %s, feedback = %s 
        WHERE id = %s
    """, (rating, feedback, service_id))
    conn.commit()
    conn.close()
    
    flash('Thank you for your feedback! ⭐')
    return redirect(url_for('customer_dashboard'))

@app.route('/update_commission', methods=['POST'])
def update_commission():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    new_rate = request.form.get('commission_rate')
    if new_rate:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value = %s WHERE key = 'tech_commission_rate'", (new_rate,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    item_id = request.form.get('item_id')
    name = request.form.get('name')
    category = request.form.get('category', 'General')
    brand = request.form.get('brand', 'Universal')
    model = request.form.get('model', 'All')
    image_url = request.form.get('image_url')
    price = float(request.form.get('price') or 0)
    purchase_price = float(request.form.get('purchase_price') or 0)
    stock = int(request.form.get('stock') or 0)
    is_for_sale = True if request.form.get('is_for_sale') else False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if item_id:
        # Get current stock to see if we are adding more
        cursor.execute("SELECT stock FROM inventory WHERE id = %s", (item_id,))
        old_stock = cursor.fetchone()['stock']
        
        cursor.execute("UPDATE inventory SET name = %s, category = %s, brand = %s, compatible_model = %s, price = %s, purchase_price = %s, stock = %s, is_for_sale = %s, image_url = %s WHERE id = %s", 
                       (name, category, brand, model, price, purchase_price, stock, is_for_sale, image_url, item_id))
        
        # If stock increased, record as a purchase/expense
        if stock > old_stock:
            added_qty = stock - old_stock
            cursor.execute("INSERT INTO stock_purchases (inventory_id, quantity, purchase_price, total_cost) VALUES (%s, %s, %s, %s)",
                           (item_id, added_qty, purchase_price, added_qty * purchase_price))
    else:
        cursor.execute("INSERT INTO inventory (name, category, brand, compatible_model, price, purchase_price, stock, is_for_sale, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                       (name, category, brand, model, price, purchase_price, stock, is_for_sale, image_url))
        new_id = cursor.fetchone()[0]
        # Record initial stock as a purchase
        if stock > 0:
            cursor.execute("INSERT INTO stock_purchases (inventory_id, quantity, purchase_price, total_cost) VALUES (%s, %s, %s, %s)",
                           (new_id, stock, purchase_price, stock * purchase_price))
            
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_inventory/<int:item_id>')
def delete_inventory(item_id):
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/create_technician', methods=['POST'])
def create_technician():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    specialization = request.form.get('specialization', 'General')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (role, name, email, phone, password, specialization) VALUES (%s, %s, %s, %s, %s, %s)",
                   ('technician', name, email, phone, password, specialization))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/update_wash_status', methods=['POST'])
def update_wash_status():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    service_id = request.form.get('service_id')
    new_status = request.form.get('status')
    
    # After finishing wash, it goes to 'Washed' so technician can generate bill
    if new_status == 'Completed':
        new_status = 'Washed'
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET status = %s WHERE id = %s", (new_status, service_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))



@app.route('/resolve_emergency/<int:id>')
def resolve_emergency(id):
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM emergency_requests WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/pay', methods=['POST'])
def pay():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    service_id = request.form.get('service_id')
    method = request.form.get('method')
    
    if method == 'online':
        return redirect(url_for('payment_gateway', service_id=service_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET payment_method = 'offline' WHERE id = %s", (service_id,))
    conn.commit()
    conn.close()
    flash('Cash collection request sent successfully.', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/payment_gateway/<int:service_id>')
def payment_gateway(service_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, v.brand, v.model, v.reg_no 
        FROM services s 
        JOIN vehicles v ON s.vehicle_id = v.id 
        WHERE s.id = %s
    """, (service_id,))
    service = cursor.fetchone()
    conn.close()
    
    if not service:
        return "Service record not found", 404
        
    total_amount = service['parts_cost'] + service['labor_cost'] + service.get('wash_cost', 0)
    
    # UPI Details - Synced with provided QR image
    vpa = "pkishore2007tnj@oksbi"  # CHANGE THIS to your UPI ID (e.g., yourname@okaxis) to receive payments
    merchant_name = "NextGen AutoCare"
    bank_name = "CANARA BANK"
    upi_phone = "9944383845"
    
    # UPI Deep Link - Simplified for maximum compatibility across all UPI apps
    encoded_name = merchant_name.replace(' ', '%20')
    upi_link = f"upi://pay?pa={vpa}&pn={encoded_name}&am={total_amount:.2f}&cu=INR&tn=NextGen_AutoCare_{service['id']}"
    
    return render_template('payment_gateway.html', 
                         service=service, 
                         total=total_amount, 
                         upi_link=upi_link, 
                         upi_id=vpa,
                         upi_phone=upi_phone,
                         bank=bank_name)

@app.route('/confirm_payment/<int:service_id>', methods=['POST'])
def confirm_payment(service_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    transaction_id = request.form.get('transaction_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Storing the transaction ID in the payment_method field for record-keeping
    payment_note = f"Online (UTR: {transaction_id})"
    cursor.execute("""
        UPDATE services 
        SET payment_status = 'Paid', 
            payment_method = %s 
        WHERE id = %s
    """, (payment_note, service_id))
    conn.commit()
    conn.close()
    
    flash('Payment confirmed! Thank you for choosing NextGen AutoCare.', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/generate_invoice/<int:service_id>')
def generate_invoice(service_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, v.reg_no, v.brand, v.model, u.name as owner_name, u.phone, u.email,
               tech.name as tech_name
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.id
        JOIN users u ON v.owner_id = u.id
        LEFT JOIN users as tech ON s.technician_id = tech.id
        WHERE s.id = %s
    """, (service_id,))
    s = cursor.fetchone()
    
    if not s:
        conn.close()
        return "Service not found", 404
        
    cursor.execute("""
        SELECT sp.*, i.name 
        FROM service_parts sp
        JOIN inventory i ON sp.part_id = i.id
        WHERE sp.service_id = %s
    """, (service_id,))
    parts = cursor.fetchall()
    conn.close()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    
    styles = getSampleStyleSheet()
    BRAND_COLOR = colors.HexColor('#1e293b')
    ACCENT_COLOR = colors.HexColor('#4f46e5')
    SUCCESS_COLOR = colors.HexColor('#10b981')
    MUTED_COLOR = colors.HexColor('#64748b')
    BORDER_COLOR = colors.HexColor('#e2e8f0')
    
    styles.add(ParagraphStyle(name='BrandTitle', parent=styles['Heading1'], fontSize=24, textColor=BRAND_COLOR, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='BrandSlogan', parent=styles['Normal'], fontSize=8, textColor=MUTED_COLOR, letterSpacing=2))
    styles.add(ParagraphStyle(name='SectionLabel', parent=styles['Normal'], fontSize=8, textColor=MUTED_COLOR, fontName='Helvetica-Bold', textTransform='uppercase'))
    styles.add(ParagraphStyle(name='SectionValue', parent=styles['Normal'], fontSize=10, textColor=colors.black, leading=14))
    styles.add(ParagraphStyle(name='TableText', parent=styles['Normal'], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name='TotalLabel', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', textColor=BRAND_COLOR, alignment=2))
    styles.add(ParagraphStyle(name='TotalAmount', parent=styles['Normal'], fontSize=16, fontName='Helvetica-Bold', textColor=ACCENT_COLOR, alignment=2))

    # Header
    header_data = [[
        [Paragraph("NextGen AutoCare", styles['BrandTitle']), Paragraph("PROFESSIONAL AUTOMOTIVE CENTER", styles['BrandSlogan'])],
        Paragraph("INVOICE", styles['Normal'])
    ]]
    header_table = Table(header_data, colWidths=[5*inch, 2.5*inch])
    elements.append(header_table)
    elements.append(Spacer(1, 40))

    # Client & Vehicle Info
    info_data = [
        [Paragraph("CLIENT DETAILS", styles['SectionLabel']), Paragraph("VEHICLE PROFILE", styles['SectionLabel']), Paragraph("ORDER SUMMARY", styles['SectionLabel'])],
        [
            Paragraph(f"<b>{s['owner_name']}</b><br/>{s['phone']}<br/>{s['email']}", styles['SectionValue']),
            Paragraph(f"<b>{s['brand']} {s['model']}</b><br/>Reg: {s['reg_no']}<br/>Type: {s['service_type'] or 'General'}", styles['SectionValue']),
            Paragraph(f"<b>ID: #INV-{s['id']:05d}</b><br/>Date: {datetime.now().strftime('%d %b %Y')}<br/>Status: <b>{s['payment_status']}</b>", styles['SectionValue'])
        ]
    ]
    info_table = Table(info_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(info_table)
    elements.append(Spacer(1, 35))

    # Table
    item_data = [[
        Paragraph("<font color='white'><b>CARE DESCRIPTION</b></font>", styles['TableText']),
        Paragraph("<font color='white'><b>QTY</b></font>", styles['TableText']),
        Paragraph("<font color='white'><b>UNIT PRICE</b></font>", styles['TableText']),
        Paragraph("<font color='white'><b>TOTAL</b></font>", styles['TableText'])
    ]]
    
    item_data.append(["Labor and Troubleshooting", "1", f"₹{s['labor_cost']:,}", f"₹{s['labor_cost']:,}"])
    if s['wash_cost'] > 0:
        item_data.append(["Premium Vehicle Wash", "1", f"₹{s['wash_cost']:,}", f"₹{s['wash_cost']:,}"])
    for p in parts:
        item_data.append([p['name'], str(p['quantity']), f"₹{p['price_at_time']:,}", f"₹{(p['price_at_time'] * p['quantity']):,}"])

    items_table = Table(item_data, colWidths=[4*inch, 1*inch, 1.25*inch, 1.25*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(items_table)
    
    total_val = s['parts_cost'] + s['labor_cost'] + s['wash_cost']
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"GRAND TOTAL: ₹{total_val:,.2f}", styles['TotalAmount']))

    doc.build(elements)
    buffer.seek(0)
    return make_response(buffer.getvalue(), 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename=Invoice_{s['reg_no']}.pdf"
    })

@app.route('/generate_job_sheet/<int:service_id>')
def generate_job_sheet(service_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, v.reg_no, v.brand, v.model, v.year, v.engine_no, v.chassis_no,
               u.name as owner_name, u.phone, u.email,
               tech.name as tech_name
        FROM services s
        JOIN vehicles v ON s.vehicle_id = v.id
        JOIN users u ON v.owner_id = u.id
        LEFT JOIN users as tech ON s.technician_id = tech.id
        WHERE s.id = %s
    """, (service_id,))
    s = cursor.fetchone()
    
    if not s:
        conn.close()
        return "Service Record not found", 404
        
    conn.close()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    
    styles = getSampleStyleSheet()
    BRAND_COLOR = colors.HexColor('#1e293b')
    ACCENT_COLOR = colors.HexColor('#4f46e5')
    MUTED_COLOR = colors.HexColor('#64748b')
    BORDER_COLOR = colors.HexColor('#e2e8f0')
    
    styles.add(ParagraphStyle(name='SheetTitle', parent=styles['Heading1'], fontSize=24, textColor=BRAND_COLOR, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SheetLabel', parent=styles['Normal'], fontSize=8, textColor=MUTED_COLOR, fontName='Helvetica-Bold', textTransform='uppercase'))
    styles.add(ParagraphStyle(name='ComplaintBox', parent=styles['Normal'], fontSize=11, textColor=colors.black, leading=16, backColor=colors.HexColor('#f8fafc'), borderPadding=10))

    # Header
    elements.append(Paragraph("SERVICE JOB SHEET", styles['SheetTitle']))
    elements.append(Paragraph(f"JOB ID: #JOB-{s['id']:05d} | DATE: {s['date']}", styles['Normal']))
    elements.append(Spacer(1, 25))

    # Info
    info_data = [
        [Paragraph("CUSTOMER", styles['SheetLabel']), Paragraph("VEHICLE", styles['SheetLabel'])],
        [
            Paragraph(f"<b>{s['owner_name']}</b><br/>{s['phone']}", styles['Normal']),
            Paragraph(f"<b>{s['brand']} {s['model']}</b><br/>{s['reg_no']}", styles['Normal'])
        ]
    ]
    elements.append(Table(info_data, colWidths=[3.75*inch, 3.75*inch], style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR)])))
    elements.append(Spacer(1, 20))

    # Complaints
    elements.append(Paragraph("REPORTED PROBLEMS / COMPLAINTS", styles['SheetLabel']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(s['problem'], styles['ComplaintBox']))
    elements.append(Spacer(1, 20))

    if s['request']:
        elements.append(Paragraph("SPECIAL REQUESTS", styles['SheetLabel']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(s['request'], styles['ComplaintBox']))
        elements.append(Spacer(1, 20))

    # Assigned Tech
    elements.append(Paragraph(f"ASSIGNED TECHNICIAN: {s['tech_name'] or 'PENDING'}", styles['Normal']))
    elements.append(Spacer(1, 100))
    
    # Signatures
    sig_data = [["_______________________", "_______________________"], ["Technician Signature", "Customer Signature"]]
    elements.append(Table(sig_data, colWidths=[3.75*inch, 3.75*inch]))

    doc.build(elements)
    buffer.seek(0)
    return make_response(buffer.getvalue(), 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename=JobSheet_{s['reg_no']}.pdf"
    })



@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    if 'user_id' not in session or session['role'] != 'admin': return redirect(url_for('login'))
    
    order_id = request.form.get('order_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check current status for cancellation logic
    cursor.execute("SELECT status, part_id, quantity FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    
    if order and order['status'] != 'Cancelled' and new_status == 'Cancelled':
        # Return stock to inventory
        cursor.execute("UPDATE inventory SET stock = stock + %s WHERE id = %s", (order['quantity'], order['part_id']))
        
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/buy/<int:part_id>')
def buy_part(part_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = %s", (part_id,))
    part = cursor.fetchone()
    conn.close()
    
    if not part:
        return "Part not found", 404
        
    return render_template('checkout.html', part=part)

@app.route('/place_order', methods=['POST'])
def place_order():
    part_id = request.form.get('part_id')
    quantity = int(request.form.get('quantity') or 1)
    name = request.form.get('name')
    phone = request.form.get('phone')
    location = request.form.get('location')
    payment_method = request.form.get('payment_method')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check Price & Stock again
    cursor.execute("SELECT price, stock FROM inventory WHERE id = %s", (part_id,))
    part = cursor.fetchone()
    
    if not part or part['stock'] < quantity:
        conn.close()
        return "Error: Item out of stock or unavailable.", 400
        
    total_amount = part['price'] * quantity
    
    # Creating Order
    cursor.execute("""
        INSERT INTO orders (customer_name, phone, location, part_id, quantity, total_amount, payment_method)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (name, phone, location, part_id, quantity, total_amount, payment_method))
    order_id = cursor.fetchone()[0]
    
    # Deduct Stock
    cursor.execute("UPDATE inventory SET stock = stock - %s WHERE id = %s", (quantity, part_id))
    
    conn.commit()
    conn.close()
    
    return render_template('order_success.html', order_id=order_id, total=total_amount)

@app.route('/vehicle_health/<int:vehicle_id>')
def vehicle_health(vehicle_id):
    """Vehicle Health Analytics Dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership or admin access
    if session['role'] == 'customer':
        cursor.execute("SELECT * FROM vehicles WHERE id = %s AND owner_id = %s", (vehicle_id, session['user_id']))
    else:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
    
    vehicle = cursor.fetchone()
    conn.close()
    
    if not vehicle:
        return "Vehicle not found or access denied", 404
    
    # Calculate health score
    health_data = calculate_vehicle_health_score(vehicle_id)
    
    if not health_data:
        return "Unable to calculate health score", 500
    
    return render_template('vehicle_health.html', vehicle=vehicle, health=health_data)

@app.route('/api/vehicle_health/<int:vehicle_id>')
def api_vehicle_health(vehicle_id):
    """API endpoint for vehicle health data (JSON)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    health_data = calculate_vehicle_health_score(vehicle_id)
    
    if not health_data:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    return jsonify(health_data)

@app.route('/update_mileage', methods=['POST'])
def update_mileage():
    """Update vehicle mileage"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    vehicle_id = request.form.get('vehicle_id')
    mileage = request.form.get('mileage')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    if session['role'] == 'customer':
        cursor.execute("SELECT * FROM vehicles WHERE id = %s AND owner_id = %s", (vehicle_id, session['user_id']))
    else:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
    
    vehicle = cursor.fetchone()
    
    if not vehicle:
        conn.close()
        return "Vehicle not found or access denied", 404
    
    # Update mileage
    cursor.execute("""
        UPDATE vehicles 
        SET current_mileage = %s, last_mileage_update = %s 
        WHERE id = %s
    """, (mileage, datetime.now().strftime('%Y-%m-%d'), vehicle_id))
    
    conn.commit()
    conn.close()
    
    # If coming from vehicle health page, redirect back there
    referrer = request.referrer
    if referrer and 'vehicle_health' in referrer:
        return redirect(referrer)
        
    if session['role'] == 'customer':
        return redirect(url_for('customer_dashboard'))
    else:
        return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
