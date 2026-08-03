import mysql.connector
import pandas as pd

# Connect to MySQL
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="logistics"
)

cursor = connection.cursor()

# ============================================================
# SHIPMENTS
# ============================================================

data = pd.read_json(
    r"shipments.json"
)
data = data.where(pd.notna(data), None)
data = data.drop_duplicates(subset=["shipment_id"])

cursor.execute("""
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    order_date DATE,
    origin VARCHAR(100),
    destination VARCHAR(100),
    weight DECIMAL(10,2),
    courier_id VARCHAR(50),
    status VARCHAR(50),
    delivery_date DATE
)
""")

cursor.execute("TRUNCATE TABLE shipments")

insert_query = """
INSERT INTO shipments (
    shipment_id, order_date, origin, destination,
    weight, courier_id, status, delivery_date
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
"""

for _, row in data.iterrows():
    cursor.execute(insert_query, (
        row["shipment_id"],
        row["order_date"],
        row["origin"],
        row["destination"],
        float(row["weight"]),
        row["courier_id"],
        row["status"],
        None if pd.isna(row["delivery_date"]) else row["delivery_date"]
    ))

# ============================================================
# SHIPMENT TRACKING
# ============================================================

csv_data = pd.read_csv(
    r"shipment_tracking.csv"
)
csv_data = csv_data.where(pd.notna(csv_data), None)
csv_data = csv_data.drop_duplicates(subset=["tracking_id"])

cursor.execute("""
CREATE TABLE IF NOT EXISTS shipment_tracking (
    tracking_id INT PRIMARY KEY,
    shipment_id VARCHAR(50),
    status VARCHAR(50),
    timestamp DATETIME
)
""")

cursor.execute("TRUNCATE TABLE shipment_tracking")

insert_query2 = """
INSERT INTO shipment_tracking (
    tracking_id, shipment_id, status, timestamp
)
VALUES (%s, %s, %s, %s)
"""

for _, row in csv_data.iterrows():
    cursor.execute(insert_query2, (
        int(row["tracking_id"]),
        row["shipment_id"],
        row["status"],
        row["timestamp"]
    ))

# ============================================================
# COURIER STAFF
# ============================================================

staff = pd.read_csv(
    r"courier_staff.csv"
)
staff = staff.where(pd.notna(staff), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS courier_staff (
    courier_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    rating DECIMAL(3,1),
    vehicle_type VARCHAR(50)
)
""")

cursor.execute("TRUNCATE TABLE courier_staff")

insert_query3 = """
INSERT INTO courier_staff (courier_id, name, rating, vehicle_type)
VALUES (%s,%s,%s,%s)
"""

for _, row in staff.iterrows():
    cursor.execute(insert_query3, (
        row["courier_id"],
        row["name"],
        row["rating"],
        row["vehicle_type"]
    ))

# ============================================================
# ROUTES
# ============================================================

routes = pd.read_csv(
    r"routes.csv"
)
routes = routes.where(pd.notna(routes), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS routes (
    route_id VARCHAR(50) PRIMARY KEY,
    origin VARCHAR(100),
    destination VARCHAR(100),
    distance_km DECIMAL(10,2),
    avg_time_hours DECIMAL(10,2)
)
""")

cursor.execute("TRUNCATE TABLE routes")

insert_query4 = """
INSERT INTO routes (route_id, origin, destination, distance_km, avg_time_hours)
VALUES (%s,%s,%s,%s,%s)
"""

for _, row in routes.iterrows():
    cursor.execute(insert_query4, (
        row["route_id"],
        row["origin"],
        row["destination"],
        row["distance_km"],
        row["avg_time_hours"]
    ))

# ============================================================
# WAREHOUSES
# ============================================================

warehouse = pd.read_json(
    r"warehouses.json"
)
warehouse = warehouse.where(pd.notna(warehouse), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id VARCHAR(50) PRIMARY KEY,
    city VARCHAR(100),
    state VARCHAR(100),
    capacity INT
)
""")

cursor.execute("TRUNCATE TABLE warehouses")

insert_query5 = """
INSERT INTO warehouses (warehouse_id, city, state, capacity)
VALUES (%s,%s,%s,%s)
"""

for _, row in warehouse.iterrows():
    cursor.execute(insert_query5, (
        row["warehouse_id"],
        row["city"],
        row["state"],
        row["capacity"]
    ))

# ============================================================
# COSTS
# ============================================================

costs = pd.read_csv(
    r"costs.csv"
)
costs = costs.where(pd.notna(costs), None)

duplicates = costs[costs.duplicated(subset=["shipment_id"], keep=False)]

# Remove duplicate shipment IDs
costs = costs.drop_duplicates(subset=["shipment_id"])

cursor.execute("""
CREATE TABLE IF NOT EXISTS costs (
    shipment_id VARCHAR(50) PRIMARY KEY,
    fuel_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    misc_cost DECIMAL(10,2)
)
""")

cursor.execute("TRUNCATE TABLE costs")

insert_query6 = """
INSERT INTO costs (shipment_id, fuel_cost, labor_cost, misc_cost)
VALUES (%s,%s,%s,%s)
"""

for _, row in costs.iterrows():
    cursor.execute(insert_query6, (
        row["shipment_id"],
        row["fuel_cost"],
        row["labor_cost"],
        row["misc_cost"]
    ))


connection.commit()
print("All tables imported successfully!")

cursor.close()
connection.close()
