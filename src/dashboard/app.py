import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os
import time

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Fetch data with cache
@st.cache_data(ttl=5)
def load_data():
    """Fetch data from the API."""
    try:
        cameras_response = requests.get(f"{API_URL}/cameras", timeout=5)
        cameras = cameras_response.json() if cameras_response.status_code == 200 else []

        stats_response = requests.get(f"{API_URL}/stats/efficiency", timeout=5)
        stats = stats_response.json() if stats_response.status_code == 200 else {}

        return cameras, stats
    except requests.exceptions.RequestException as e:
        # Avoid spamming errors on UI if auto-refresh is on
        return [], {}

def process_stats(stats):
    """Convert stats dict to DataFrame for plotting."""
    data = []
    if not stats:
        return pd.DataFrame(columns=["Camera", "Zone", "Count"])

    for camera_id, zones in stats.items():
        for zone, count in zones.items():
            data.append({"Camera": camera_id, "Zone": zone, "Count": count})
    return pd.DataFrame(data)

def render_sidebar(cameras):
    """Render the sidebar for camera selection."""
    st.sidebar.title("Dashboard")

    # If API is down, cameras might be empty
    if not cameras:
        st.sidebar.warning("No cameras detected.")
        if st.sidebar.button("Refresh"):
            st.cache_data.clear()
            st.rerun()
        return "All"

    camera_ids = [c.get('id', f"Camera {i}") for i, c in enumerate(cameras)]
    selected_camera = st.sidebar.selectbox("Select Camera", ["All"] + camera_ids)

    # Show camera status in sidebar
    st.sidebar.subheader("Camera Status")
    for cam in cameras:
        status = cam.get('status', 'Offline')
        color = "🟢" if status == 'Online' else "🔴"
        st.sidebar.write(f"{color} {cam.get('id', 'Unknown')}: {status}")

    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    return selected_camera

def render_kpis(df, selected_camera):
    """Render KPIs."""
    st.header("Key Performance Indicators")

    if df.empty:
        st.info("No event data available.")
        return

    if selected_camera == "All":
        # Aggregate totals
        total_events = df["Count"].sum()
        active_cameras = df["Camera"].nunique()

        # Display aggregate metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Events (All Cameras)", int(total_events))
        col2.metric("Active Cameras", active_cameras)

        st.subheader("Camera Performance Grid")
        # Display a grid of cards for each camera
        cameras = df["Camera"].unique()
        if len(cameras) > 0:
            cols = st.columns(3) # 3 columns grid
            for i, cam in enumerate(cameras):
                cam_df = df[df["Camera"] == cam]
                cam_total = cam_df["Count"].sum()
                if not cam_df.empty:
                    top_zone_row = cam_df.loc[cam_df["Count"].idxmax()]
                    top_zone = top_zone_row['Zone']
                else:
                    top_zone = "N/A"

                with cols[i % 3]:
                    st.metric(label=cam, value=int(cam_total), delta=f"Top: {top_zone}")
        else:
             st.info("No camera data to display in grid.")

    else:
        cam_df = df[df["Camera"] == selected_camera]
        if cam_df.empty:
            st.info(f"No events recorded for {selected_camera}")
            return

        total_events = cam_df["Count"].sum()
        top_zone_row = cam_df.loc[cam_df["Count"].idxmax()]
        top_zone = f"{top_zone_row['Zone']} ({top_zone_row['Count']})"

        col1, col2 = st.columns(2)
        col1.metric("Total Events", int(total_events))
        col2.metric("Top Zone", top_zone)

def render_charts(df, selected_camera):
    """Render charts."""
    st.header("Efficiency Analysis")

    if df.empty:
        return

    if selected_camera == "All":
        st.subheader("Activity Overview")

        # Aggregate by Camera
        cam_agg = df.groupby("Camera")["Count"].sum().reset_index()
        fig_cam = px.bar(cam_agg, x="Camera", y="Count", title="Total Events per Camera", color="Camera")
        st.plotly_chart(fig_cam, use_container_width=True)

        # Detailed by Zone
        st.subheader("Zone Details")
        fig_zone = px.bar(df, x="Camera", y="Count", color="Zone", title="Events Distribution by Zone")
        st.plotly_chart(fig_zone, use_container_width=True)

    else:
        st.subheader(f"Activity in {selected_camera}")
        cam_df = df[df["Camera"] == selected_camera]

        if cam_df.empty:
             return

        fig = px.bar(cam_df, x="Zone", y="Count", title="Events per Zone", color="Zone")
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="Multi-Camera Dashboard", layout="wide")
    st.title("Multi-Camera Tracking Dashboard")

    cameras, stats = load_data()

    df = process_stats(stats)

    selected_camera = render_sidebar(cameras)

    render_kpis(df, selected_camera)
    render_charts(df, selected_camera)

if __name__ == "__main__":
    main()
