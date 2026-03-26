# AI-Based Vehicle Analytics with Health Score

## 🎯 Overview

This feature implements an intelligent vehicle health monitoring system that analyzes vehicle data and provides predictive maintenance insights without manual inspection.

## ✅ System Functionality

The system provides the following capabilities:

### 1. **Vehicle Mileage Analysis**
- Tracks current mileage and mileage update history
- Calculates average yearly mileage based on vehicle age
- Identifies high-usage patterns that may require more frequent maintenance

### 2. **Service History Analysis**
- Analyzes frequency and regularity of service intervals
- Detects overdue services and maintenance gaps
- Tracks service completion patterns

### 3. **Repair Frequency Analysis**
- Identifies repair vs. routine maintenance patterns
- Detects major repairs (₹5000+)
- Calculates repair-to-service ratio

### 4. **Vehicle Health Condition Prediction**
- Generates a comprehensive health score (0-100)
- Categorizes health status: Excellent (85+), Good (70-84), Fair (50-69), Poor (<50)
- Provides color-coded visual indicators

### 5. **Next Maintenance Schedule Suggestion**
- Predicts next service date based on last service
- Recommends maintenance based on mileage milestones
- Provides specific maintenance tasks for different mileage ranges

### 6. **Dynamic Vehicle Health Score**
The health score is calculated based on multiple weighted factors:
- **Mileage Analysis** (20 points): Annual mileage patterns
- **Service Frequency** (25 points): Regularity and timeliness of services
- **Repair Frequency** (30 points): Repair ratio and severity
- **Cost Analysis** (15 points): Average service costs
- **Vehicle Age** (10 points): Age-based degradation factor

### 7. **Smart Insights & Recommendations**
Instead of manual inspection, the system provides:
- AI-generated insights about vehicle condition
- Actionable recommendations for maintenance
- Predictive alerts for potential issues
- Mileage-based maintenance suggestions

## 🚀 Features

### Customer Dashboard Integration
- New "Vehicle Health" tab in the navigation menu
- Quick health score overview for all vehicles
- Real-time health data fetching via AJAX
- Direct links to detailed analytics

### Detailed Health Dashboard
- **Visual Health Score**: Animated circular progress indicator
- **Health Status Badge**: Color-coded status (Excellent/Good/Fair/Poor)
- **Key Metrics Display**:
  - Total services completed
  - Repair count
  - Current mileage
  - Vehicle age
  - Average service cost
- **AI-Powered Insights**: Smart analysis of vehicle condition
- **Smart Recommendations**: Actionable maintenance advice
- **Predictive Maintenance Schedule**: Mileage-based suggestions
- **Next Service Date**: Calculated based on service history
- **Mileage Update Form**: Easy mileage tracking

### API Endpoints
- `GET /vehicle_health/<vehicle_id>`: Full health dashboard
- `GET /api/vehicle_health/<vehicle_id>`: JSON health data
- `POST /update_mileage`: Update vehicle mileage

## 📊 Health Score Calculation

The AI algorithm analyzes:

1. **Mileage Patterns**
   - High annual mileage (>20,000 km/year): -15 points
   - Above average (>15,000 km/year): -8 points
   - Normal usage: No deduction

2. **Service Frequency**
   - Overdue services (>180 days): -20 points
   - Due soon (>150 days): -10 points
   - No service history: -25 points
   - Irregular intervals: -5 points

3. **Repair Analysis**
   - High repair ratio (>60%): -25 points
   - Moderate repair ratio (>40%): -15 points
   - Multiple major repairs (>2): -10 points

4. **Cost Analysis**
   - High average cost (>₹8,000): -15 points
   - Above average (>₹5,000): -8 points

5. **Vehicle Age**
   - Older vehicles (>10 years): -10 points
   - Mature vehicles (>7 years): -5 points

## 🎨 User Interface

### Design Features
- **Modern Gradient Design**: Purple gradient theme matching the existing dashboard
- **Animated Health Score**: Circular progress animation on page load
- **Responsive Layout**: Works on all screen sizes
- **Color-Coded Indicators**: 
  - Green (85+): Excellent condition
  - Blue (70-84): Good condition
  - Orange (50-69): Fair condition
  - Red (<50): Poor condition
- **Interactive Cards**: Hover effects and smooth transitions
- **Real-time Updates**: AJAX-based health score loading

## 📱 Usage

### For Customers

1. **View Health Overview**
   - Navigate to "Vehicle Health" tab in dashboard
   - See health scores for all vehicles at a glance
   - Click "View Detailed Analytics" for any vehicle

2. **Detailed Analysis**
   - View comprehensive health score with visual indicator
   - Read AI-generated insights about vehicle condition
   - Review smart recommendations
   - Check predictive maintenance schedule
   - See next recommended service date

3. **Update Mileage**
   - Scroll to "Update Vehicle Mileage" section
   - Enter current mileage
   - Submit to recalculate health score

### For Administrators
- Access health analytics for any vehicle
- Monitor fleet health across all customers
- Use insights for proactive customer outreach

## 🔧 Technical Implementation

### Database Changes
Added to `vehicles` table:
- `current_mileage` (INTEGER): Current odometer reading
- `last_mileage_update` (TEXT): Date of last mileage update

### Backend Functions
- `calculate_vehicle_health_score(vehicle_id)`: Core AI analytics engine
  - Analyzes service history
  - Calculates health score
  - Generates insights and recommendations
  - Returns comprehensive health data dictionary

### Frontend Components
- `vehicle_health.html`: Full-featured health dashboard
- Customer dashboard integration with AJAX health cards
- Real-time health score fetching

## 🎯 Benefits

1. **Proactive Maintenance**: Predict issues before they become serious
2. **Cost Savings**: Avoid expensive repairs through timely maintenance
3. **Data-Driven Decisions**: Make informed choices about vehicle care
4. **Convenience**: No manual inspection required
5. **Transparency**: Clear insights into vehicle condition
6. **Peace of Mind**: Know your vehicle's health status at all times

## 📈 Future Enhancements

Potential improvements:
- Machine learning model for more accurate predictions
- Integration with OBD-II devices for real-time diagnostics
- Comparative analysis with similar vehicles
- Maintenance cost forecasting
- Integration with parts inventory for automatic recommendations
- Push notifications for critical health alerts
- Historical health score tracking and trends

## 🔐 Security

- Authentication required for all health endpoints
- Ownership verification for customer access
- Admin override for fleet management
- Secure mileage update validation

## 📝 Example Health Insights

The system generates insights like:
- "⚠️ High annual mileage: 25,000 km/year"
- "✅ Last serviced 45 days ago"
- "🔴 Service overdue by 30 days"
- "💰 High average service cost: ₹9,500"
- "✅ Low repair frequency: 2/8 services"

## 🎓 Maintenance Suggestions

Based on mileage:
- **0-20k km**: Basic service (oil change, basic inspection)
- **20-50k km**: Standard service (oil, filters, tire rotation)
- **50-100k km**: Intermediate service (brakes, coolant, spark plugs)
- **100k+ km**: Major service (timing belt, suspension, transmission)

---

**Built with AI-powered analytics to keep your vehicles running smoothly! 🚗✨**
