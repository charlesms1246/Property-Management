# Property Management System

A web-based property management system built with Flask and SQLite. This system helps property owners manage their properties, tenants, maintenance requests, and financial records.

## Features

- **User Management**
  - User registration and authentication
  - Role-based access control
  - Secure password handling

- **Property Management**
  - Add, edit, and delete properties
  - Track property status (vacant/occupied)
  - View property details and financial summary

- **Tenant Management**
  - Add, edit, and remove tenants
  - Track lease agreements
  - View tenant history

- **Maintenance Tracking**
  - Create and track maintenance requests
  - Update request status
  - View maintenance history

- **Financial Management**
  - Record rent payments
  - Track late payments
  - Calculate late fees
  - View financial summaries

- **Database Management**
  - View database tables and schemas
  - Access table contents
  - Export data

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd Property-Management
```

2. **Create and activate virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure the application**
- Create a `.env` file in the project root with the following content:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

5. **Initialize the database**
```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade

# (Optional) Add sample data
python sample_data.py
```

6. **Run the application**
```bash
python run.py
```

The application will be available at http://localhost:5000

## Usage

1. **Registration and Login**
   - Register a new account
   - Log in with your credentials

2. **Dashboard**
   - View property overview
   - Check recent maintenance requests
   - Monitor upcoming payments

3. **Properties**
   - Add new properties
   - View property details
   - Edit property information
   - Delete properties

4. **Tenants**
   - Add new tenants
   - View tenant details
   - Record rent payments
   - Track lease agreements

5. **Maintenance**
   - Create maintenance requests
   - Update request status
   - View maintenance history

6. **Database View**
   - Access database tables
   - View table schemas
   - Check table contents

## Project Structure

```
Property-Management/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── properties.py
│   │   ├── tenants.py
│   │   └── maintenance.py
│   └── templates/
│       ├── base.html
│       ├── auth/
│       ├── properties/
│       ├── tenants/
│       └── maintenance/
├── instance/
│   └── property_management.db
├── migrations/
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.

## Database Schema

### Tables

1. **User**
   - `id` (Primary Key)
   - `username` (Unique)
   - `email` (Unique)
   - `password_hash`
   - `created_at`

2. **Property**
   - `id` (Primary Key)
   - `name`
   - `address`
   - `type` (apartment, house, commercial)
   - `status` (vacant, occupied)
   - `rent_amount`
   - `owner_id` (Foreign Key to User)
   - `created_at`

3. **Tenant**
   - `id` (Primary Key)
   - `name`
   - `email`
   - `phone`
   - `property_id` (Foreign Key to Property)
   - `lease_start`
   - `lease_end`
   - `created_at`

4. **MaintenanceRequest**
   - `id` (Primary Key)
   - `property_id` (Foreign Key to Property)
   - `title`
   - `description`
   - `status` (pending, in_progress, completed)
   - `created_at`
   - `updated_at`

5. **RentPayment**
   - `id` (Primary Key)
   - `tenant_id` (Foreign Key to Tenant)
   - `amount`
   - `payment_date`
   - `status` (pending, paid, late)
   - `created_at`

### Views

1. **PropertyFinancialSummary**
   ```sql
   CREATE VIEW property_financial_summary AS
   SELECT 
       p.id as property_id,
       p.name as property_name,
       COUNT(t.id) as total_tenants,
       SUM(CASE WHEN rp.status = 'paid' THEN rp.amount ELSE 0 END) as total_paid,
       COUNT(CASE WHEN rp.status = 'late' THEN 1 END) as late_payments
   FROM property p
   LEFT JOIN tenant t ON p.id = t.property_id
   LEFT JOIN rent_payment rp ON t.id = rp.tenant_id
   GROUP BY p.id, p.name;
   ```

2. **MaintenanceHistory**
   ```sql
   CREATE VIEW maintenance_history AS
   SELECT 
       mr.id,
       p.name as property_name,
       mr.title,
       mr.description,
       mr.status,
       mr.created_at,
       mr.updated_at
   FROM maintenance_request mr
   JOIN property p ON mr.property_id = p.id;
   ```

### Triggers

1. **Update Property Status**
   ```sql
   CREATE TRIGGER update_property_status
   AFTER INSERT OR UPDATE OR DELETE ON tenant
   FOR EACH ROW
   BEGIN
       UPDATE property
       SET status = CASE
           WHEN EXISTS (
               SELECT 1 FROM tenant 
               WHERE property_id = NEW.property_id
           ) THEN 'occupied'
           ELSE 'vacant'
       END
       WHERE id = NEW.property_id;
   END;
   ```

2. **Maintenance Request Timestamp**
   ```sql
   CREATE TRIGGER maintenance_request_timestamp
   BEFORE UPDATE ON maintenance_request
   FOR EACH ROW
   BEGIN
       SET NEW.updated_at = CURRENT_TIMESTAMP;
   END;
   ```

### Functions

1. **Calculate Late Fee**
   ```sql
   CREATE FUNCTION calculate_late_fee(days_late INT, rent_amount DECIMAL)
   RETURNS DECIMAL
   BEGIN
       DECLARE late_fee DECIMAL;
       SET late_fee = CASE
           WHEN days_late <= 0 THEN 0
           WHEN days_late <= 5 THEN rent_amount * 0.05
           WHEN days_late <= 10 THEN rent_amount * 0.10
           ELSE rent_amount * 0.15
       END;
       RETURN late_fee;
   END;
   ```

2. **Lease Status**
   ```sql
   CREATE FUNCTION get_lease_status(lease_start DATE, lease_end DATE)
   RETURNS VARCHAR(20)
   BEGIN
       DECLARE current_date DATE;
       SET current_date = CURRENT_DATE;
       
       RETURN CASE
           WHEN current_date < lease_start THEN 'upcoming'
           WHEN current_date BETWEEN lease_start AND lease_end THEN 'active'
           ELSE 'expired'
       END;
   END;
   ```

### Indexes

1. **Property Indexes**
   ```sql
   CREATE INDEX idx_property_owner ON property(owner_id);
   CREATE INDEX idx_property_status ON property(status);
   ```

2. **Tenant Indexes**
   ```sql
   CREATE INDEX idx_tenant_property ON tenant(property_id);
   CREATE INDEX idx_tenant_lease ON tenant(lease_start, lease_end);
   ```

3. **Maintenance Indexes**
   ```sql
   CREATE INDEX idx_maintenance_property ON maintenance_request(property_id);
   CREATE INDEX idx_maintenance_status ON maintenance_request(status);
   ```

4. **Payment Indexes**
   ```sql
   CREATE INDEX idx_payment_tenant ON rent_payment(tenant_id);
   CREATE INDEX idx_payment_status ON rent_payment(status);
   CREATE INDEX idx_payment_date ON rent_payment(payment_date);
   ``` 