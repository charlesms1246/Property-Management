-- Drop existing objects if they exist
DROP TRIGGER IF EXISTS update_property_status;
DROP TRIGGER IF EXISTS maintenance_request_timestamp;
DROP FUNCTION IF EXISTS calculate_late_fee;
DROP FUNCTION IF EXISTS get_lease_status;
DROP VIEW IF EXISTS property_financial_summary;
DROP VIEW IF EXISTS maintenance_history;

-- Create tables
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS property (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'vacant',
    rent_amount DECIMAL(10,2) NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    property_id INTEGER NOT NULL,
    lease_start DATE NOT NULL,
    lease_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES property (id)
);

CREATE TABLE IF NOT EXISTS maintenance_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES property (id),
    FOREIGN KEY (tenant_id) REFERENCES tenant (id)
);

CREATE TABLE IF NOT EXISTS rent_payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant (id)
);

-- Create views
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

-- Create triggers
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

CREATE TRIGGER maintenance_request_timestamp
BEFORE UPDATE ON maintenance_requests
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

-- Create functions
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

-- Create indexes
CREATE INDEX idx_property_owner ON property(owner_id);
CREATE INDEX idx_property_status ON property(status);
CREATE INDEX idx_tenant_property ON tenant(property_id);
CREATE INDEX idx_tenant_lease ON tenant(lease_start, lease_end);
CREATE INDEX idx_maintenance_property ON maintenance_requests(property_id);
CREATE INDEX idx_maintenance_status ON maintenance_requests(status);
CREATE INDEX idx_maintenance_priority ON maintenance_requests(priority);
CREATE INDEX idx_payment_tenant ON rent_payment(tenant_id);
CREATE INDEX idx_payment_status ON rent_payment(status);
CREATE INDEX idx_payment_date ON rent_payment(payment_date); 