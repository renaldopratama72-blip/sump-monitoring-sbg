import streamlit as st
import pandas as pd
from sqlalchemy import text

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
    
    # Load Sump
    df_s = conn.query("SELECT * FROM sump", ttl=0)
    if not df_s.empty:
        # Normalize column names from Postgres (lowercase) to App format
        df_s.columns = map(str.lower, df_s.columns)
        df_s['tanggal'] = pd.to_datetime(df_s['tanggal'])
        df_s = df_s.rename(columns={
            "elevasi_air": "Elevasi Air (m)", "critical_elevation": "Critical Elevation (m)",
            "volume_air_survey": "Volume Air Survey (m3)", "plan_curah_hujan": "Plan Curah Hujan (mm)",
            "curah_hujan": "Curah Hujan (mm)", "actual_catchment": "Actual Catchment (Ha)",
            "groundwater": "Groundwater (m3)", "tanggal": "Tanggal", "site": "Site", "pit": "Pit", "status": "Status"
        })

    # Load Pompa
    df_p = conn.query("SELECT * FROM pompa", ttl=0)
    if not df_p.empty:
        df_p.columns = map(str.lower, df_p.columns)
        df_p['tanggal'] = pd.to_datetime(df_p['tanggal'])
        df_p = df_p.rename(columns={
            "unit_code": "Unit Code", "debit_plan": "Debit Plan (m3/h)",
            "debit_actual": "Debit Actual (m3/h)", "ewh_plan": "EWH Plan", "ewh_actual": "EWH Actual",
            "tanggal": "Tanggal", "site": "Site", "pit": "Pit"
        })
    
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

    # Use SQLAlchemy engine via st.connection
    engine = conn.engine 
    s_save.to_sql('sump', engine, if_exists='replace', index=False)
    p_save.to_sql('pompa', engine, if_exists='replace', index=False)
    