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

def reset_db():
    """DROPS and recreates tables."""
    conn = get_connection()
    with conn.session as session:
        session.execute(text("DROP TABLE IF EXISTS sump"))
        session.execute(text("DROP TABLE IF EXISTS pompa"))
        session.commit()
    init_db()

def load_data():
    """Fetch all data from Neon."""
    init_db()
    conn = get_connection()
    
    # --- LOAD SUMP ---
    try:
        df_s = conn.query("SELECT * FROM sump", ttl=0)
    except Exception:
        df_s = pd.DataFrame()

    df_s.columns = map(str.lower, df_s.columns)
    if not df_s.empty:
        df_s['tanggal'] = pd.to_datetime(df_s['tanggal'])
    
    df_s = df_s.rename(columns={
        "elevasi_air": "Elevasi Air (m)", "critical_elevation": "Critical Elevation (m)",
        "volume_air_survey": "Volume Air Survey (m3)", "plan_curah_hujan": "Plan Curah Hujan (mm)",
        "curah_hujan": "Curah Hujan (mm)", "actual_catchment": "Actual Catchment (Ha)",
        "groundwater": "Groundwater (m3)", "tanggal": "Tanggal", "site": "Site", "pit": "Pit", "status": "Status"
    })

    expected_sump_cols = [
        "Tanggal", "Site", "Pit", "Elevasi Air (m)", "Critical Elevation (m)",
        "Volume Air Survey (m3)", "Plan Curah Hujan (mm)", "Curah Hujan (mm)",
        "Actual Catchment (Ha)", "Groundwater (m3)", "Status"
    ]
    if df_s.empty or not all(col in df_s.columns for col in expected_sump_cols):
         df_s = pd.DataFrame(columns=expected_sump_cols)

    # --- LOAD POMPA ---
    try:
        df_p = conn.query("SELECT * FROM pompa", ttl=0)
    except Exception:
        df_p = pd.DataFrame()
        
    df_p.columns = map(str.lower, df_p.columns)
    if not df_p.empty:
        df_p['tanggal'] = pd.to_datetime(df_p['tanggal'])

    df_p = df_p.rename(columns={
        "unit_code": "Unit Code", "debit_plan": "Debit Plan (m3/h)",
        "debit_actual": "Debit Actual (m3/h)", "ewh_plan": "EWH Plan", "ewh_actual": "EWH Actual",
        "tanggal": "Tanggal", "site": "Site", "pit": "Pit"
    })

    expected_pompa_cols = [
        "Tanggal", "Site", "Pit", "Unit Code", 
        "Debit Plan (m3/h)", "Debit Actual (m3/h)", "EWH Plan", "EWH Actual"
    ]
    if df_p.empty or not all(col in df_p.columns for col in expected_pompa_cols):
        df_p = pd.DataFrame(columns=expected_pompa_cols)
    
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
    """Bulk replace tables."""
    conn = get_connection()
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
    s_save.columns = map(str.lower, s_save.columns)
    p_save.columns = map(str.lower, p_save.columns)

    engine = conn.engine 
    s_save.to_sql('sump', engine, if_exists='replace', index=False)
    p_save.to_sql('pompa', engine, if_exists='replace', index=False)

def generate_dummy_data():
    """Generates dummy data matching the logic from app_previous.py."""
    conn = get_connection()
    
    # 1. Config based on PREVIOUS APP logic
    dummy_prefix = "dummy_" # Keeping prefix so we can delete it easily later
    
    # We map the real names to include the 'dummy_' prefix so deletion works safely
    init_map = {
        f"{dummy_prefix}Lais Coal Mine (LCM)": [f"{dummy_prefix}Sump Wijaya Barat", f"{dummy_prefix}Sump Wijaya Timur"],
        f"{dummy_prefix}Wiraduta Sejahtera Langgeng (WSL)": [f"{dummy_prefix}Sump F01", f"{dummy_prefix}Sump F02"],
        f"{dummy_prefix}Nusantara Energy (NE)": [f"{dummy_prefix}Sump S8"]
    }
    
    units = [f"{dummy_prefix}WP-01", f"{dummy_prefix}WP-02"]
    
    # 2. Generate Data Loop (30 Days)
    today = date.today()
    sump_rows = []
    pump_rows = []
    
    for i in range(30):
        d = today - timedelta(days=i)
        
        for site, pits in init_map.items():
            for pit in pits:
                # --- Sump Data (Sine Wave Logic) ---
                # Logic copied from app_previous.py: elev = 10.0 + (np.sin(i/10) * 2)
                elev = 10.0 + (np.sin(i/10) * 2)
                
                sump_rows.append({
                    "tanggal": d, 
                    "site": site, 
                    "pit": pit, 
                    "elevasi_air": round(elev, 2), 
                    "critical_elevation": 13.0,
                    "volume_air_survey": int(elev * 5000), 
                    "plan_curah_hujan": 20.0, 
                    "curah_hujan": np.random.randint(0, 40),
                    "actual_catchment": 25.0, 
                    "groundwater": 0.0,
                    "status": "BAHAYA" if elev > 13.0 else "AMAN"
                })
                
                # --- Pump Data ---
                for u in units:
                    pump_rows.append({
                        "tanggal": d, 
                        "site": site, 
                        "pit": pit, 
                        "unit_code": u,
                        "debit_plan": 500, 
                        "debit_actual": np.random.randint(400, 500), 
                        "ewh_plan": 20.0, 
                        "ewh_actual": round(np.random.uniform(15, 20), 1)
                    })
        
    # 3. Save to DB
    df_s_dummy = pd.DataFrame(sump_rows)
    df_p_dummy = pd.DataFrame(pump_rows)
    
    engine = conn.engine
    df_s_dummy.to_sql('sump', engine, if_exists='append', index=False)
    df_p_dummy.to_sql('pompa', engine, if_exists='append', index=False)

def delete_dummy_data():
    """Deletes all data where Site starts with 'dummy_'."""
    conn = get_connection()
    with conn.session as session:
        session.execute(text("DELETE FROM sump WHERE Site LIKE 'dummy_%'"))
        session.execute(text("DELETE FROM pompa WHERE Site LIKE 'dummy_%'"))
        session.commit()