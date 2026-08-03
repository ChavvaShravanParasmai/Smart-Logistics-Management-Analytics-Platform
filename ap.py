import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Smart Logistics Dashboard", layout="wide")

# ============================================================
# DATABASE CONNECTION
# ============================================================
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="logistics"
)

shipments = pd.read_sql("SELECT * FROM shipments", connection)
courier = pd.read_sql("SELECT * FROM courier_staff", connection)
tracking = pd.read_sql("SELECT * FROM shipment_tracking", connection)
routes = pd.read_sql("SELECT * FROM routes", connection)
warehouses = pd.read_sql("SELECT * FROM warehouses", connection)
costs = pd.read_sql("SELECT * FROM costs", connection)

connection.close()

# ============================================================
# DERIVED / FEATURE-ENGINEERED COLUMNS
# ============================================================
shipments["order_date"] = pd.to_datetime(shipments["order_date"])
shipments["delivery_date"] = pd.to_datetime(shipments["delivery_date"])
shipments["delivery_time_days"] = (
    shipments["delivery_date"] - shipments["order_date"]
).dt.days

costs["total_cost"] = costs["fuel_cost"] + costs["labor_cost"] + costs["misc_cost"]

st.title("Smart Logistics Management Dashboard")

# ============================================================
# SHIPMENT SEARCH & FILTERING (sidebar)
# ============================================================
st.sidebar.header("Filters")

status_options = sorted(shipments["status"].dropna().unique().tolist())
status_filter = st.sidebar.multiselect("Status", status_options, default=status_options)

origin_options = sorted(shipments["origin"].dropna().unique().tolist())
origin_filter = st.sidebar.multiselect("Origin", origin_options)

dest_options = sorted(shipments["destination"].dropna().unique().tolist())
dest_filter = st.sidebar.multiselect("Destination", dest_options)

courier_options = courier[["courier_id", "name"]].dropna()
courier_name_to_id = dict(zip(courier_options["name"], courier_options["courier_id"]))
courier_filter_names = st.sidebar.multiselect("Courier", sorted(courier_name_to_id.keys()))

min_date = shipments["order_date"].min()
max_date = shipments["order_date"].max()
date_range = st.sidebar.date_input(
    "Order Date Range", value=(min_date.date(), max_date.date())
)

filtered = shipments.copy()

if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
if origin_filter:
    filtered = filtered[filtered["origin"].isin(origin_filter)]
if dest_filter:
    filtered = filtered[filtered["destination"].isin(dest_filter)]
if courier_filter_names:
    ids = [courier_name_to_id[n] for n in courier_filter_names]
    filtered = filtered[filtered["courier_id"].isin(ids)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[
        (filtered["order_date"] >= start) & (filtered["order_date"] <= end)
    ]

st.write(f"Showing **{len(filtered)}** of **{len(shipments)}** shipments after filters")

st.write("### Search Shipment by ID")
shipment_id = st.text_input("Enter Shipment ID")
if shipment_id:
    result = shipments[shipments["shipment_id"] == shipment_id]
    if len(result) > 0:
        st.success("Shipment Found")
        st.dataframe(result)

        
        history = tracking[tracking["shipment_id"] == shipment_id].sort_values("timestamp")
        if len(history) > 0:
            st.write("Tracking History")
            st.dataframe(history)
        else:
            st.info("No tracking history found for this shipment.")
    else:
        st.error("Shipment Not Found")

# ============================================================
# B. OPERATIONAL KPIs
# ============================================================
st.write("## Operational KPIs")

total = len(filtered)
delivered = len(filtered[filtered["status"] == "Delivered"])
cancelled = len(filtered[filtered["status"] == "Cancelled"])
delivered_pct = (delivered / total * 100) if total else 0
cancelled_pct = (cancelled / total * 100) if total else 0
avg_delivery_time = filtered.loc[filtered["status"] == "Delivered", "delivery_time_days"].mean()

filtered_costs = costs[costs["shipment_id"].isin(filtered["shipment_id"])]
total_op_cost = filtered_costs["total_cost"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Shipments", total)
k2.metric("Delivered %", f"{delivered_pct:.1f}%")
k3.metric("Cancelled %", f"{cancelled_pct:.1f}%")
k4.metric("Avg Delivery Time", f"{avg_delivery_time:.1f} days" if pd.notna(avg_delivery_time) else "N/A")
k5.metric("Total Operational Cost", f"${total_op_cost:,.2f}")

st.write("### Shipment Status Breakdown")
st.bar_chart(filtered["status"].value_counts())

# ============================================================
# C. ANALYTICAL VIEWS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Delivery Performance", "Courier Performance",
    "Cost Analytics", "Cancellation Analysis", "Warehouse Insights"
])

# ---- 1. Delivery Performance Insights -------------------------------
with tab1:
    st.write("#### Average Delivery Time per Route")
    delivered_ship = shipments[shipments["status"] == "Delivered"].copy()
    route_perf = (
        delivered_ship.groupby(["origin", "destination"])["delivery_time_days"]
        .mean()
        .reset_index()
        .rename(columns={"delivery_time_days": "avg_delivery_days"})
    )
    route_perf = route_perf.merge(routes, on=["origin", "destination"], how="left")
    # Assumption: "expected days" = avg_time_hours / 24, since routes give hours
    # but our shipment dates only have day-level precision.
    route_perf["expected_days"] = route_perf["avg_time_hours"] / 24
    route_perf["delay_days"] = route_perf["avg_delivery_days"] - route_perf["expected_days"]
    st.dataframe(route_perf.sort_values("avg_delivery_days", ascending=False))

    st.write("#### Most Delayed Routes (actual vs expected)")
    most_delayed = route_perf.dropna(subset=["delay_days"]).sort_values(
        "delay_days", ascending=False
    ).head(15)
    st.dataframe(most_delayed[["origin", "destination", "avg_delivery_days", "expected_days", "delay_days"]])

    st.write("#### Delivery Time vs Distance")
    scatter_df = delivered_ship.merge(routes, on=["origin", "destination"], how="left")
    scatter_df = scatter_df.dropna(subset=["distance_km", "delivery_time_days"])
    if len(scatter_df) > 0:
        st.scatter_chart(scatter_df, x="distance_km", y="delivery_time_days")
    else:
        st.info("Not enough matched route data to plot distance vs delivery time.")

# ---- 2. Courier Performance ------------------------------------------
with tab2:
    st.write("#### Shipments Handled per Courier")
    per_courier = (
        shipments.groupby("courier_id").size().reset_index(name="total_shipments")
    )
    per_courier = per_courier.merge(courier, on="courier_id", how="left")
    st.dataframe(per_courier.sort_values("total_shipments", ascending=False))

    st.write("#### On-Time Delivery % per Courier")

    delivered_routes = shipments[shipments["status"] == "Delivered"].merge(
        routes, on=["origin", "destination"], how="left"
    )
    delivered_routes["expected_days"] = delivered_routes["avg_time_hours"] / 24
    delivered_routes = delivered_routes.dropna(subset=["expected_days"])
    delivered_routes["on_time"] = (
        delivered_routes["delivery_time_days"] <= delivered_routes["expected_days"]
    )
    on_time_pct = (
        delivered_routes.groupby("courier_id")["on_time"]
        .mean()
        .reset_index()
        .rename(columns={"on_time": "on_time_pct"})
    )
    on_time_pct["on_time_pct"] = (on_time_pct["on_time_pct"] * 100).round(1)
    on_time_pct = on_time_pct.merge(courier, on="courier_id", how="left")
    st.dataframe(on_time_pct.sort_values("on_time_pct", ascending=False))

    st.write("#### Average Rating Comparison")
    st.bar_chart(courier.set_index("name")["rating"])

# ---- 3. Cost Analytics -------------------------------------------------
with tab3:
    st.write("#### Total Cost per Shipment")
    cost_view = costs.merge(
        shipments[["shipment_id", "origin", "destination"]], on="shipment_id", how="left"
    )
    st.dataframe(cost_view.sort_values("total_cost", ascending=False))

    st.write("#### Cost per Route")
    cost_route = (
        cost_view.groupby(["origin", "destination"])["total_cost"]
        .mean()
        .reset_index()
        .rename(columns={"total_cost": "avg_total_cost"})
        .sort_values("avg_total_cost", ascending=False)
    )
    st.dataframe(cost_route)

    st.write("#### Fuel vs Labor vs Misc Contribution")
    contrib = pd.DataFrame({
        "component": ["Fuel", "Labor", "Misc"],
        "amount": [
            costs["fuel_cost"].sum(),
            costs["labor_cost"].sum(),
            costs["misc_cost"].sum(),
        ]
    })
    st.bar_chart(contrib.set_index("component"))

    st.write("#### High-Cost Shipments (Top 20)")
    st.dataframe(cost_view.sort_values("total_cost", ascending=False).head(20))

# ---- 4. Cancellation Analysis -------------------------------------------
with tab4:
    cancelled_ship = shipments[shipments["status"] == "Cancelled"]

    st.write("#### Cancellation Rate by Origin")
    cancel_origin = cancelled_ship.groupby("origin").size().sort_values(ascending=False)
    st.bar_chart(cancel_origin)

    st.write("#### Cancellation Rate by Courier")
    cancel_courier = cancelled_ship.merge(courier, on="courier_id", how="left")
    cancel_by_courier = cancel_courier.groupby("name").size().sort_values(ascending=False)
    st.bar_chart(cancel_by_courier)

    st.write("#### Time-to-Cancellation")
    
    if len(tracking) > 0:
        tracking["timestamp"] = pd.to_datetime(tracking["timestamp"])
        first_event = tracking.groupby("shipment_id")["timestamp"].min().rename("first_ts")
        cancel_event = tracking[tracking["status"] == "Cancelled"].groupby("shipment_id")["timestamp"].min().rename("cancel_ts")
        ttc = pd.concat([first_event, cancel_event], axis=1).dropna()
        ttc["hours_to_cancel"] = (ttc["cancel_ts"] - ttc["first_ts"]).dt.total_seconds() / 3600
        st.metric("Average Time to Cancellation", f"{ttc['hours_to_cancel'].mean():.1f} hours")
        st.dataframe(ttc.reset_index())
    else:
        st.info("No tracking data available yet — re-run data.py with the fixed script.")

# ---- 5. Warehouse Insights ------------------------------------------------
with tab5:
    st.write("#### Warehouse Capacity Comparison")
    st.bar_chart(warehouses.set_index("city")["capacity"])

    st.write("#### High-Traffic Warehouse Cities")

    wh_cities = set(warehouses["city"])
    origin_hits = shipments[shipments["origin"].isin(wh_cities)]["origin"].value_counts()
    dest_hits = shipments[shipments["destination"].isin(wh_cities)]["destination"].value_counts()
    traffic = origin_hits.add(dest_hits, fill_value=0).sort_values(ascending=False)
    st.bar_chart(traffic.head(20))
    st.dataframe(traffic.reset_index().rename(columns={"index": "city", 0: "shipment_count"}).head(20))
