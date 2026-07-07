import streamlit as st
import pandas as pd
import mysql.connector

# Database Connection
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="logistics"
)

# Read tables
shipments = pd.read_sql("SELECT * FROM shipments", connection)
courier = pd.read_sql("SELECT * FROM courier_staff", connection)
tracking = pd.read_sql("SELECT * FROM shipment_tracking", connection)
routes = pd.read_sql("SELECT * FROM routes", connection)
warehouses = pd.read_sql("SELECT * FROM warehouses", connection)
costs = pd.read_sql("SELECT * FROM costs", connection)

# Title
st.title("Smart Logistics Management Dashboard")

st.write("### Dashboard Summary")

total = len(shipments)
delivered = len(shipments[shipments["status"] == "Delivered"])
cancelled = len(shipments[shipments["status"] == "Cancelled"])

col1, col2, col3 = st.columns(3)

col1.metric("Total Shipments", total)
col2.metric("Delivered", delivered)
col3.metric("Cancelled", cancelled)

st.write("### Shipment Status")

status = shipments["status"].value_counts()
st.bar_chart(status)

st.write("### Courier Staff")
st.dataframe(courier)

st.write("### Shipment Tracking")
st.dataframe(tracking)

st.write("### Routes")
st.dataframe(routes)

st.write("### Warehouses")
st.dataframe(warehouses)

st.write("### Costs")
st.dataframe(costs)

st.write("### Search Shipment")

shipment_id = st.text_input("Enter Shipment ID")

if shipment_id != "":

    result = shipments[shipments["shipment_id"] == shipment_id]

    if len(result) > 0:
        st.write("Shipment Found")
        st.dataframe(result)
    else:
        st.write("Shipment Not Found")

st.write("### All Shipments")
st.dataframe(shipments)

query = """
SELECT
origin,
destination,
COUNT(*) AS total_shipments
FROM shipments
GROUP BY origin, destination
ORDER BY total_shipments DESC
"""

routes_data = pd.read_sql(query, connection)

st.write("### Busiest Routes")
st.dataframe(routes_data)

st.dataframe(costs)

costs["total_cost"] = (
    costs["fuel_cost"] +
    costs["labor_cost"] +
    costs["misc_cost"]
)

st.write("Total Operational Cost")

st.write(costs["total_cost"].sum())

query = """
SELECT
c.name,
COUNT(s.shipment_id) AS Total_Shipments
FROM courier_staff c
JOIN shipments s
ON c.courier_id=s.courier_id
GROUP BY c.name
ORDER BY Total_Shipments DESC
"""

courier_performance = pd.read_sql(query, connection)

st.write("Courier Performance")

st.dataframe(courier_performance)

query = """
SELECT
origin,
COUNT(*) AS Cancelled
FROM shipments
WHERE status='Cancelled'
GROUP BY origin
ORDER BY Cancelled DESC
"""

cancel = pd.read_sql(query, connection)

st.write("Cancellation Pattern")

st.bar_chart(cancel.set_index("origin"))

query = """
SELECT
status,
COUNT(*) AS Total
FROM shipments
GROUP BY status
"""

performance = pd.read_sql(query, connection)

st.write("Delivery Performance")

st.bar_chart(performance.set_index("status"))



connection.close()