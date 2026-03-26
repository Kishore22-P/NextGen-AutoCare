# Dynamic Technician Load Balancer ⚖️

## Overview
The Dynamic Technician Load Balancer is an intelligent auto-assignment system that automatically assigns the most suitable technician to each service request based on two key criteria:

1. **Matching Specialization** - Technicians with expertise in the requested service type are prioritized
2. **Least Active Services** - Among qualified technicians, the one with the lowest current workload is selected

## How It Works

### Algorithm Flow

```
Customer Books Service → Selects Service Type → Load Balancer Activates
                                                          ↓
                                    ┌─────────────────────────────────────┐
                                    │  Step 1: Find Specialist Match      │
                                    │  Query technicians with matching    │
                                    │  specialization, ordered by active  │
                                    │  services (ascending)                │
                                    └─────────────────────────────────────┘
                                                          ↓
                                    ┌─────────────────────────────────────┐
                                    │  Specialist Found?                   │
                                    │  YES → Assign specialist with       │
                                    │        least workload                │
                                    │  NO  → Go to Step 2                 │
                                    └─────────────────────────────────────┘
                                                          ↓
                                    ┌─────────────────────────────────────┐
                                    │  Step 2: Fallback Assignment        │
                                    │  Find ANY technician with least     │
                                    │  active services (General)           │
                                    └─────────────────────────────────────┘
                                                          ↓
                                    ┌─────────────────────────────────────┐
                                    │  Service Status Updated              │
                                    │  - Technician assigned: "Assigned"  │
                                    │  - No technician: "Pending"         │
                                    └─────────────────────────────────────┘
```

### Service Types Supported

- **General** - Routine maintenance and general repairs
- **Engine** - Engine diagnostics, repairs, and overhauls
- **Electrical** - Electrical systems, wiring, and electronics
- **Transmission** - Transmission repairs and maintenance
- **Brakes** - Brake systems and ABS
- **AC/Cooling** - Air conditioning and cooling systems
- **Body Work** - Body repairs, painting, and detailing

## Implementation Details

### Backend Function (`app.py`)

```python
def auto_assign_technician(service_type):
    """
    Dynamic Technician Load Balancer ⚖️
    
    Automatically assigns technician with:
    1. Matching specialization to service type
    2. Least active services (workload balancing)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Step 1: Find specialist with least workload
    cursor.execute("""
        SELECT u.id, u.name, u.specialization,
               COUNT(CASE WHEN s.status NOT IN ('Completed', 'Ready for Wash', 'Washing') 
                     THEN 1 END) as active_services
        FROM users u
        LEFT JOIN services s ON u.id = s.technician_id
        WHERE u.role = 'technician' AND u.specialization = %s
        GROUP BY u.id, u.name, u.specialization
        ORDER BY active_services ASC
        LIMIT 1
    """, (service_type,))
    
    specialist = cursor.fetchone()
    if specialist:
        conn.close()
        return specialist['id']
    
    # Step 2: Fallback to any available technician
    cursor.execute("""
        SELECT u.id, u.name, u.specialization,
               COUNT(CASE WHEN s.status NOT IN ('Completed', 'Ready for Wash', 'Washing') 
                     THEN 1 END) as active_services
        FROM users u
        LEFT JOIN services s ON u.id = s.technician_id
        WHERE u.role = 'technician'
        GROUP BY u.id, u.name, u.specialization
        ORDER BY active_services ASC
        LIMIT 1
    """)
    
    any_tech = cursor.fetchone()
    conn.close()
    
    return any_tech['id'] if any_tech else None
```

### Database Schema

The system uses the existing `users` table with the `specialization` column:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    password TEXT NOT NULL,
    specialization TEXT  -- Added for load balancing
);
```

### Frontend Integration

#### Customer Dashboard (`customer_dashboard.html`)
- **Service Type Dropdown**: Customers select the type of service needed when booking
- The selected service type is sent to the backend for intelligent assignment

#### Admin Dashboard (`admin_dashboard.html`)
- **Technician Table Enhancements**:
  - **Specialization Column**: Shows each technician's area of expertise
  - **Active Load Column**: Displays current workload with visual indicators:
    - 🟢 Green (0-2 active services) - Available
    - 🟡 Yellow (3-4 active services) - Moderate load
    - 🔴 Red (5+ active services) - High load
  
- **Technician Creation Form**: Includes specialization selection

## Benefits

### 1. **Optimal Resource Utilization**
- Distributes workload evenly across all technicians
- Prevents technician burnout and bottlenecks
- Maximizes service center capacity

### 2. **Quality Service Delivery**
- Matches specialists to appropriate jobs
- Reduces service time and errors
- Improves customer satisfaction

### 3. **Transparency & Visibility**
- Admin can monitor workload distribution in real-time
- Visual indicators make it easy to spot imbalances
- Data-driven decision making for hiring and scheduling

### 4. **Scalability**
- Automatically adapts as technicians are added or removed
- No manual intervention required
- Handles varying service volumes efficiently

## Usage Examples

### Example 1: Engine Repair Request
```
Customer books: "Engine Repair"
Service Type: Engine

Load Balancer:
1. Searches for technicians with specialization = "Engine"
2. Finds: 
   - Tech A (Engine, 2 active services)
   - Tech B (Engine, 5 active services)
3. Assigns to Tech A (least workload)
```

### Example 2: No Specialist Available
```
Customer books: "Transmission Service"
Service Type: Transmission

Load Balancer:
1. Searches for technicians with specialization = "Transmission"
2. No specialist found
3. Fallback: Assigns to any technician with least workload
   - Tech C (General, 1 active service) ✓
```

### Example 3: All Technicians Busy
```
Customer books: "Brake Service"
Service Type: Brakes

Load Balancer:
1. Searches for brake specialists
2. All have high workload
3. Assigns to specialist with lowest workload (even if busy)
4. Service marked as "Assigned" for queue management
```

## Monitoring & Analytics

### Admin Dashboard Metrics
- **Active Load per Technician**: Real-time workload visualization
- **Completed Jobs**: Historical performance tracking
- **Revenue per Technician**: Financial performance metrics
- **Specialization Distribution**: Team skill coverage

### Visual Indicators
- **Glowing Dots**: Color-coded workload status
  - Cyan: No active services (available)
  - Green: 1-2 active services (optimal)
  - Yellow: 3-4 active services (moderate)
  - Red: 5+ active services (overloaded)

## Future Enhancements

1. **Priority Queue**: VIP customers or emergency services get priority
2. **Skill Level Matching**: Match job complexity to technician experience
3. **Geographic Assignment**: For mobile/on-site services
4. **Time-based Balancing**: Consider estimated completion times, not just count
5. **Predictive Analytics**: ML-based workload prediction and optimization
6. **Technician Preferences**: Allow technicians to set preferred service types
7. **Customer Ratings**: Factor in technician ratings for assignment

## Testing the Feature

### Test Scenario 1: Create Technicians with Different Specializations
1. Login as Admin
2. Navigate to "Technicians" tab
3. Click "+ Add Technician"
4. Create technicians with various specializations:
   - John (Engine Specialist)
   - Sarah (Electrical Systems)
   - Mike (General Service)

### Test Scenario 2: Book Services and Observe Assignment
1. Login as Customer
2. Book an "Engine Repair" service
3. Check Admin Dashboard → See John assigned (Engine specialist)
4. Book another "Engine Repair"
5. If John has more active services than other Engine specialists, the next one gets assigned

### Test Scenario 3: Monitor Workload Distribution
1. Login as Admin
2. Navigate to "Technicians" tab
3. Observe "Active Load" column
4. Book multiple services
5. Watch the load balancer distribute work evenly

## Conclusion

The Dynamic Technician Load Balancer transforms the service center from manual assignment chaos to an intelligent, automated, and optimized workflow. It ensures:

✅ Right technician for the right job
✅ Balanced workload distribution
✅ Improved service quality
✅ Better resource utilization
✅ Real-time visibility and control

This feature is production-ready and will significantly improve operational efficiency!
