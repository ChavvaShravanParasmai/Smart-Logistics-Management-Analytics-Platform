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

#Reading JSON
data = pd.read_json(
    r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\shipments.json"
)

#Reading CSV
csv_data = pd.read_csv(r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\shipment_tracking.csv")

#NaN with None
data = data.where(pd.notna(data), None)
csv_data = csv_data.where(pd.notna(csv_data), None)

# Removing duplicate ids
data = data.drop_duplicates(subset=["shipment_id"])
csv_data = csv_data.drop_duplicates(subset=["shipment_id"])


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

cursor.execute("""
CREATE TABLE IF NOT EXISTS shipment_tracking (
    tracking_id INT,
    shipment_id VARCHAR(50),
    status VARCHAR(50),
    timestamp DATETIME
)
""")


cursor.execute("TRUNCATE TABLE shipments")
cursor.execute("TRUNCATE TABLE shipment_tracking")


insert_query = """
INSERT INTO shipments (
    shipment_id,
    order_date,
    origin,
    destination,
    weight,
    courier_id,
    status,
    delivery_date
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

insert_query2 = """
INSERT INTO shipment_tracking (
    shipment_id,
    status
)
VALUES (%s, %s)
"""
for _, row in csv_data.iterrows():

    cursor.execute(insert_query2,(
        row["shipment_id"],
        row["status"]
    )           
                   )
    

cursor.execute("""
CREATE TABLE IF NOT EXISTS shipment_tracking (
    tracking_id INT,
    shipment_id VARCHAR(50),
    status VARCHAR(50),
    timestamp DATETIME
)
""")

cursor.execute("TRUNCATE TABLE shipment_tracking")

# Reading CSV
staff = pd.read_csv(
    r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\courier_staff.csv"
)

staff = staff.where(pd.notna(staff), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS courier_staff (
    courier_id VARCHAR(50),
    name VARCHAR(100),
    rating DECIMAL(3,1),
    vehicle_type VARCHAR(50)
)
""")

cursor.execute("TRUNCATE TABLE courier_staff")

insert_query3 = """
INSERT INTO courier_staff (
    courier_id,
    name,
    rating,
    vehicle_type
)
VALUES (%s,%s,%s,%s)
"""

for _, row in staff.iterrows():

    cursor.execute(insert_query3,(
        row["courier_id"],
        row["name"],
        row["rating"],
        row["vehicle_type"]
    ))


# Routes 

# Reading CSV
routes = pd.read_csv(
    r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\routes.csv"
)

routes = routes.where(pd.notna(routes), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS routes (
    route_id VARCHAR(50),
    origin VARCHAR(100),
    destination VARCHAR(100),
    distance_km DECIMAL(10,2),
    avg_time_hours DECIMAL(10,2)
)
""")

cursor.execute("TRUNCATE TABLE routes")

insert_query4 = """
INSERT INTO routes (
    route_id,
    origin,
    destination,
    distance_km,
    avg_time_hours
)
VALUES (%s,%s,%s,%s,%s)
"""

for _, row in routes.iterrows():

    cursor.execute(insert_query4,(
        row["route_id"],
        row["origin"],
        row["destination"],
        row["distance_km"],
        row["avg_time_hours"]
    ))


#Warehouses

# Readign JSON
warehouse = pd.read_json(
    r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\warehouses.json"
)

warehouse = warehouse.where(pd.notna(warehouse), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    capacity INT
)
""")

cursor.execute("TRUNCATE TABLE warehouses")

insert_query5 = """
INSERT INTO warehouses (
    warehouse_id,
    city,
    state,
    capacity
)
VALUES (%s,%s,%s,%s)
"""

for _, row in warehouse.iterrows():

    cursor.execute(insert_query5,(
        row["warehouse_id"],
        row["city"],
        row["state"],
        row["capacity"]
    ))

#Costs
# Read CSV
costs = pd.read_csv(
    r"C:\Users\shrav\OneDrive\Desktop\Smart Logistics Management & Analytics Platform\Datasets\costs.csv"
)

costs = costs.where(pd.notna(costs), None)

cursor.execute("""
CREATE TABLE IF NOT EXISTS costs (
    shipment_id VARCHAR(50),
    fuel_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    misc_cost DECIMAL(10,2)
)
""")

cursor.execute("TRUNCATE TABLE costs")

insert_query6 = """
INSERT INTO costs (
    shipment_id,
    fuel_cost,
    labor_cost,
    misc_cost
)
VALUES (%s,%s,%s,%s)
"""

for _, row in costs.iterrows():

    cursor.execute(insert_query6,(
        row["shipment_id"],
        row["fuel_cost"],
        row["labor_cost"],
        row["misc_cost"]
    ))


# Shipments Table

query = "SELECT * FROM shipments"
df = pd.read_sql(query, connection)

print("Shipments")
print(df.head())


# Total Shipments

query = "SELECT COUNT(*) AS Total_Shipments FROM shipments"
print(pd.read_sql(query, connection))

# Shipments by Status

query = """
SELECT status, COUNT(*) AS Total
FROM shipments
GROUP BY status
"""
print(pd.read_sql(query, connection))


# Average Weight
query = """
SELECT AVG(weight) AS Average_Weight
FROM shipments
"""
print(pd.read_sql(query, connection))


# 5. Top Heavy Shipments

query = """
SELECT *
FROM shipments
ORDER BY weight DESC
LIMIT 10
"""
print(pd.read_sql(query, connection))


# Shipments by Origin

query = """
SELECT origin, COUNT(*) AS Total
FROM shipments
GROUP BY origin
ORDER BY Total DESC
"""
print(pd.read_sql(query, connection))


# Shipments by Destination

query = """
SELECT destination, COUNT(*) AS Total
FROM shipments
GROUP BY destination
ORDER BY Total DESC
"""
print(pd.read_sql(query, connection))


# Courier Performance

query = """
SELECT
c.name,
COUNT(s.shipment_id) AS Total_Shipments
FROM courier_staff c
JOIN shipments s
ON c.courier_id = s.courier_id
GROUP BY c.name
ORDER BY Total_Shipments DESC
"""
print(pd.read_sql(query, connection))


# Average Courier Rating

query = """
SELECT AVG(rating) AS Average_Rating
FROM courier_staff
"""
print(pd.read_sql(query, connection))


# Pending Deliveries

query = """
SELECT *
FROM shipments
WHERE delivery_date IS NULL
"""
print(pd.read_sql(query, connection))

connection.close()



# connection.commit()

# print("All tables imported successfully!")

# cursor.close()
# connection.close()


