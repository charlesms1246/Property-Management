# Property Management System - Database Design

## Table of Contents
1. [Database Overview](#database-overview)
2. [Entity-Relationship Diagram](#entity-relationship-diagram)
3. [Tables](#tables)
4. [Views](#views)
5. [Triggers](#triggers)
6. [Functions](#functions)
7. [Indexes](#indexes)
8. [Data Types and Constraints](#data-types-and-constraints)
9. [Business Rules](#business-rules)

## Database Overview
The Property Management System database is designed to manage properties, tenants, maintenance requests, and rent payments. It uses SQLite as the database engine and implements various database objects to ensure data integrity and provide useful views of the data.

## Entity-Relationship Diagram
See `er_diagram.puml` for the visual representation of the database schema.

## Tables

### 1. User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Description**: Stores user account information for property owners/managers.
**Constraints**:
- Username must be unique
- Email must be unique
- Password hash is required
- Created_at is automatically set

### 2. Property Table
```sql
CREATE TABLE property (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('house', 'apartment', 'commercial')),
    status VARCHAR(20) DEFAULT 'vacant' CHECK (status IN ('vacant', 'occupied')),
    rent_amount DECIMAL(10,2) NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);
```
**Description**: Stores property information and ownership details.
**Constraints**:
- Property type must be one of: house, apartment, commercial
- Status must be one of: vacant, occupied
- Rent amount must be positive
- Owner must exist in user table

### 3. Tenant Table
```sql
CREATE TABLE tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    property_id INTEGER NOT NULL,
    lease_start DATE NOT NULL,
    lease_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES property (id),
    CHECK (lease_end > lease_start)
);
```
**Description**: Stores tenant information and lease details.
**Constraints**:
- Property must exist
- Lease end date must be after lease start date
- Email and phone are required

### 4. Maintenance Request Table
```sql
CREATE TABLE maintenance_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES property (id),
    FOREIGN KEY (tenant_id) REFERENCES tenant (id)
);
```
**Description**: Tracks maintenance requests and their status.
**Constraints**:
- Status must be one of: pending, in_progress, completed
- Priority must be one of: low, medium, high
- Property and tenant must exist
- Completed_at must be after created_at (enforced by application)

### 5. Rent Payment Table
```sql
CREATE TABLE rent_payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'late')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant (id),
    CHECK (amount > 0)
);
```
**Description**: Records rent payments and their status.
**Constraints**:
- Status must be one of: pending, paid, late
- Amount must be positive
- Tenant must exist

## Views

### 1. Property Financial Summary
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
**Purpose**: Provides financial overview of each property.

### 2. Maintenance History
```sql
CREATE VIEW maintenance_history AS
SELECT 
    mr.id,
    p.name as property_name,
    t.name as tenant_name,
    mr.title,
    mr.description,
    mr.status,
    mr.priority,
    mr.created_at,
    mr.completed_at
FROM maintenance_requests mr
JOIN property p ON mr.property_id = p.id
JOIN tenant t ON mr.tenant_id = t.id;
```
**Purpose**: Tracks maintenance request history with property and tenant details.

## Triggers

### 1. Update Property Status
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
**Purpose**: Automatically updates property status based on tenant occupancy.

### 2. Maintenance Request Timestamp
```sql
CREATE TRIGGER maintenance_request_timestamp
BEFORE UPDATE ON maintenance_requests
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;
```
**Purpose**: Maintains audit trail of maintenance request updates.

## Functions

### 1. Calculate Late Fee
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
**Purpose**: Calculates late fees based on days late and rent amount.

### 2. Get Lease Status
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
**Purpose**: Determines lease status based on dates.

## Indexes

### Property Table Indexes
```sql
CREATE INDEX idx_property_owner ON property(owner_id);
CREATE INDEX idx_property_status ON property(status);
```

### Tenant Table Indexes
```sql
CREATE INDEX idx_tenant_property ON tenant(property_id);
CREATE INDEX idx_tenant_lease ON tenant(lease_start, lease_end);
```

### Maintenance Request Indexes
```sql
CREATE INDEX idx_maintenance_property ON maintenance_requests(property_id);
CREATE INDEX idx_maintenance_status ON maintenance_requests(status);
CREATE INDEX idx_maintenance_priority ON maintenance_requests(priority);
```

### Rent Payment Indexes
```sql
CREATE INDEX idx_payment_tenant ON rent_payment(tenant_id);
CREATE INDEX idx_payment_status ON rent_payment(status);
CREATE INDEX idx_payment_date ON rent_payment(payment_date);
```

## Data Types and Constraints

### Common Data Types
- INTEGER: For IDs and counts
- VARCHAR(n): For strings with length limit
- TEXT: For longer text fields
- DECIMAL(p,s): For monetary values
- DATE: For dates
- TIMESTAMP: For date-time values

### Common Constraints
- PRIMARY KEY: Unique identifier
- FOREIGN KEY: Referential integrity
- UNIQUE: No duplicate values
- NOT NULL: Required field
- CHECK: Value validation
- DEFAULT: Default values

## Business Rules

1. **Property Management**
   - A property can have multiple tenants
   - Property status automatically updates based on tenant occupancy
   - Property type must be one of: house, apartment, commercial

2. **Tenant Management**
   - A tenant must be associated with a property
   - Lease end date must be after start date
   - Tenant contact information is required

3. **Maintenance Requests**
   - Requests must be associated with both property and tenant
   - Status must follow the workflow: pending → in_progress → completed
   - Priority levels: low, medium, high

4. **Rent Payments**
   - Payments must be associated with a tenant
   - Amount must be positive
   - Status can be: pending, paid, late
   - Late fees are calculated based on days late

5. **User Management**
   - Usernames and emails must be unique
   - Password must be hashed
   - Users can own multiple properties 