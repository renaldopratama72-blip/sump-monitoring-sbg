import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import text
from datetime import date, timedelta
import random

# Initialize connection
def get_connection():
    return st.connection("neon", type="sql")

def init_db():
    """Create tables in Neon if they don't exist."""
    conn = get_connection()
    with conn.session as session:
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS sump (
                Tanggal DATE, Site TEXT, Pit TEXT, Elevasi_Air REAL, Critical_Elevation REAL,
                Volume_Air_Survey REAL, Plan_Curah_Hujan REAL, Curah_Hujan REAL,
                Actual_Catchment REAL, Groundwater REAL, Status TEXT
            )'''))
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS pompa (
                Tanggal DATE, Site TEXT, Pit TEXT, Unit_Code TEXT,
                Debit_Plan REAL, Debit_Actual REAL, EWH_Plan REAL, EWH_Actual REAL
            )'''))
        session.commit()

def load_data():
    """Fetch all data from Neon."""
    init_db()
    conn = get_connection()
    
    # --- LOAD SUMP ---
    df_s = conn.query("SELECT * FROM sump", ttl=0)
    
    # Ensure columns are lowercase first (Postgres standard)
    df_s.columns = map(str.lower, df_s.columns)
    
    # Handle Date Column
    if not df_s.empty:
        df_s['tanggal'] = pd.to_datetime(df_s['tanggal'])
    
    # Apply Standard Naming
    df_s = df_s.rename(columns={
        "elevasi_air": "Elevasi Air (m)", "critical_elevation": "Critical Elevation (m)",
        "volume_air_survey": "Volume Air Survey (m3)", "plan_curah_hujan": "Plan Curah Hujan (mm)",
        "curah_hujan": "Curah Hujan (mm)", "actual_catchment": "Actual Catchment (Ha)",
        "groundwater": "Groundwater (m3)", "tanggal": "Tanggal", "site": "Site", "pit": "Pit", "status": "Status"
    })

    if df_s.empty and 'Site' not in df_s.columns:
         df_s = pd.DataFrame(columns=[
            "Tanggal", "Site", "Pit", "Elevasi Air (m)", "Critical Elevation (m)",
            "Volume Air Survey (m3)", "Plan Curah Hujan (mm)", "Curah Hujan (mm)",
            "Actual Catchment (Ha)", "Groundwater (m3)", "Status"
        ])

    # --- LOAD POMPA ---
    df_p = conn.query("SELECT * FROM pompa", ttl=0)
    
    df_p.columns = map(str.lower, df_p.columns)
    
    if not df_p.empty:
        df_p['tanggal'] = pd.to_datetime(df_p['tanggal'])

    df_p = df_p.rename(columns={
        "unit_code": "Unit Code", "debit_plan": "Debit Plan (m3/h)",
        "debit_actual": "Debit Actual (m3/h)", "ewh_plan": "EWH Plan", "ewh_actual": "EWH Actual",
        "tanggal": "Tanggal", "site": "Site", "pit": "Pit"
    })

    if df_p.empty and 'Site' not in df_p.columns:
        df_p = pd.DataFrame(columns=[
            "Tanggal", "Site", "Pit", "Unit Code", 
            "Debit Plan (m3/h)", "Debit Actual (m3/h)", "EWH Plan", "EWH Actual"
        ])
    
    return df_s, df_p

def save_new_sump(data):
    """Insert single sump record."""
    conn = get_connection()
    with conn.session as session:
        query = text("""INSERT INTO sump (Tanggal, Site, Pit, Elevasi_Air, Critical_Elevation, Volume_Air_Survey, 
                     Plan_Curah_Hujan, Curah_Hujan, Actual_Catchment, Groundwater, Status) 
                     VALUES (:t, :s, :p, :ea, :ce, :vs, :rp, :ra, :ac, :gw, :st)""")
        session.execute(query, {
            "t": data['Tanggal'], "s": data['Site'], "p": data['Pit'],
            "ea": data['Elevasi Air (m)'], "ce": data['Critical Elevation (m)'], "vs": data['Volume Air Survey (m3)'],
            "rp": data['Plan Curah Hujan (mm)'], "ra": data['Curah Hujan (mm)'], "ac": data['Actual Catchment (Ha)'],
            "gw": data['Groundwater (m3)'], "st": data['Status']
        })
        session.commit()

def save_new_pompa(data):
    """Insert single pump record."""
    conn = get_connection()
    with conn.session as session:
        query = text("""INSERT INTO pompa (Tanggal, Site, Pit, Unit_Code, Debit_Plan, Debit_Actual, EWH_Plan, EWH_Actual) 
                     VALUES (:t, :s, :p, :uc, :dp, :da, :ep, :ea)""")
        session.execute(query, {
            "t": data['Tanggal'], "s": data['Site'], "p": data['Pit'],
            "uc": data['Unit Code'], "dp": data['Debit Plan (m3/h)'], "da": data['Debit Actual (m3/h)'],
            "ep": data['EWH Plan'], "ea": data['EWH Actual']
        })
        session.commit()

def overwrite_full_db(df_s, df_p):
    """Bulk replace tables (used in Edit tab)."""
    conn = get_connection()
    
    # Prepare Dataframes
    s_save = df_s.rename(columns={
        "Elevasi Air (m)": "elevasi_air", "Critical Elevation (m)": "critical_elevation",
        "Volume Air Survey (m3)": "volume_air_survey", "Plan Curah Hujan (mm)": "plan_curah_hujan",
        "Curah Hujan (mm)": "curah_hujan", "Actual Catchment (Ha)": "actual_catchment",
        "Groundwater (m3)": "groundwater"
    })
    
    p_save = df_p.rename(columns={
        "Unit Code": "unit_code", "Debit Plan (m3/h)": "debit_plan",
        "Debit Actual (m3/h)": "debit_actual", "EWH Plan": "ewh_plan", "EWH Actual": "ewh_actual"
    })

    # Ensure columns are lowercase to match Postgres schema
    s_save.columns = map(str.lower, s_save.columns)
    p_save.columns = map(str.lower, p_save.columns)

    engine = conn.engine 
    s_save.to_sql('sump', engine, if_exists='replace', index=False)
    p_save.to_sql('pompa', engine, if_exists='replace', index=False)

# --- NEW FUNCTIONS FOR DUMMY DATA ---

def generate_dummy_data():
    """Generates 30 days of dummy data for visualization testing."""
    conn = get_connection()
    
    # 1. Config
    dummy_prefix = "dummy_"
    site_name = f"{dummy_prefix}Site_Demo"
    pit_name = f"{dummy_prefix}Pit_Alpha"
    pump_units = [f"{dummy_prefix}Pump_01", f"{dummy_prefix}Pump_02"]
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date)
    
    sump_rows = []
    pump_rows = []
    
    # 2. Generate Loop
    vol_tracker = 50000 # Starting volume
    
    for d in dates:
        # Simulate Rain & GW
        rain = random.choices([0, 0, 5, 15, 45], weights=[0.6, 0.1, 0.1, 0.1, 0.1])[0]
        gw = 1000
        inflow = (rain * 25 * 10) + gw
        
        # Simulate Pumps
        outflow = 0
        for p_unit in pump_units:
            # Random performance
            ewh_act = random.uniform(10, 20)
            deb_act = random.uniform(400, 550)
            outflow += (ewh_act * deb_act)
            
            pump_rows.append({
                "tanggal": d, "site": site_name, "pit": pit_name, "unit_code": p_unit,
                "debit_plan": 500, "debit_actual": deb_act, 
                "ewh_plan": 20, "ewh_actual": ewh_act
            })
            
        # Update Sump Logic
        vol_tracker = max(0, vol_tracker + inflow - outflow)
        elev = 10 + (vol_tracker / 10000) # Rough correlation
        
        sump_rows.append({
            "tanggal": d, "site": site_name, "pit": pit_name, 
            "elevasi_air": elev, "critical_elevation": 14.0,
            "volume_air_survey": vol_tracker, 
            "plan_curah_hujan": 15.0, "curah_hujan": rain,
            "actual_catchment": 25.0, "groundwater": gw,
            "status": "BAHAYA" if elev > 14 else "AMAN"
        })
        
    # 3. Save to DB using append
    df_s_dummy = pd.DataFrame(sump_rows)
    df_p_dummy = pd.DataFrame(pump_rows)
    
    # Append to existing tables
    engine = conn.engine
    df_s_dummy.to_sql('sump', engine, if_exists='append', index=False)
    df_p_dummy.to_sql('pompa', engine, if_exists='append', index=False)

def delete_dummy_data():
    """Deletes all data where Site starts with 'dummy_'."""
    conn = get_connection()
    with conn.session as session:
        # Safe deletion using parameter matching or direct string check on known prefix
        session.execute(text("DELETE FROM sump WHERE Site LIKE 'dummy_%'"))
        session.execute(text("DELETE FROM pompa WHERE Site LIKE 'dummy_%'"))
        session.commit()