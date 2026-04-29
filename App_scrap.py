import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
from supabase import create_client
import streamlit as st

# ================= SUPABASE =================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CONFIG =================
st.set_page_config(page_title="Control de Scrap", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= SESSION =================
def init_state():
    defaults = {
        "pantalla": "menu",
        "parte": "",
        "maquina": "",
        "libras": "",
        "ultimo_scan": "",
        "abrir_teclado": False,
        "form_uid": 0,
        "fecha": datetime.now().date(),
        "nuevo_uid": 0,
        "causa_qr": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ================= SUPABASE HELPERS =================
def leer_tabla(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error en {tabla}: {e}")
        return pd.DataFrame()

def insertar_tabla(tabla, data):
    try:
        supabase.table(tabla).insert(data).execute()
    except Exception as e:
        st.error(f"Error insertando en {tabla}: {e}")

def guardar_scrap(data):
    insertar_tabla("ScrapRegistrado", data)

# ================= HEADER =================
def render_header(titulo):
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("⬅️"):
            st.session_state.pantalla = "menu"
            st.rerun()
    with col2:
        st.markdown(f"## {titulo}")

# ================= MENU =================
def menu():
    st.title("Control de Scrap")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Escaneo"):
            st.session_state.pantalla = "escaneo"
            st.rerun()
        if st.button("➕ Nuevo"):
            st.session_state.pantalla = "nuevo"
            st.rerun()

    with col2:
        if st.button("📊 Historial"):
            st.session_state.pantalla = "historial"
            st.rerun()
        if st.button("📈 Gráficos"):
            st.session_state.pantalla = "graficos"
            st.rerun()

# ================= ESCANEO =================
def escaneo():
    render_header("Escaneo")

    df_maquinas = leer_tabla("Maquinas")
    maquinas = df_maquinas["nombre_maquina"].dropna().tolist()

    df_partes = leer_tabla("NumerosParte")
    df_planes = leer_tabla("PlanesAccion")
    df_maquinistas = leer_tabla("Maquinistas")

    maquina = st.selectbox("Máquina", maquinas)
    st.session_state.maquina = maquina

    partes = df_partes[df_partes["maquina"] == maquina]["numero_parte"].tolist()
    parte = st.selectbox("Parte", partes)
    st.session_state.parte = parte

    causa = st.text_input("Causa (QR)")
    plan = st.selectbox("Plan", df_planes["plan"].tolist())

    firmas = df_maquinistas[df_maquinistas["maquina"] == maquina]["nombre"].tolist()
    firma = st.selectbox("Firma", firmas)

    libras = st.text_input("Libras")
    fecha = st.date_input("Fecha", value=datetime.now().date())

    if st.button("Guardar"):
        data = {
            "Fecha": str(fecha),
            "Maquina": maquina,
            "Parte": parte,
            "Causa": causa,
            "Plan_Accion": plan,
            "Libras": float(libras),
            "Firma": firma
        }
        guardar_scrap(data)
        st.success("Guardado")
        st.rerun()

# ================= NUEVO =================
def nuevo():
    render_header("Nuevo")

    with st.expander("Máquina"):
        nombre = st.text_input("Nombre máquina")
        if st.button("Guardar máquina"):
            insertar_tabla("Maquinas", {"nombre_maquina": nombre})
            st.success("OK")

    with st.expander("Causa"):
        causa = st.text_input("Causa")
        if st.button("Guardar causa"):
            insertar_tabla("Causas", {"causa": causa})
            st.success("OK")

    with st.expander("Plan"):
        plan = st.text_input("Plan")
        if st.button("Guardar plan"):
            insertar_tabla("PlanesAccion", {"plan": plan})
            st.success("OK")

    with st.expander("Parte"):
        df_maquinas = leer_tabla("Maquinas")
        maquinas = df_maquinas["nombre_maquina"].tolist()

        maq = st.selectbox("Máquina", maquinas)
        parte = st.text_input("Número parte")

        if st.button("Guardar parte"):
            insertar_tabla("NumerosParte", {
                "numero_parte": parte,
                "maquina": maq
            })
            st.success("OK")

    with st.expander("Maquinista"):
        df_maquinas = leer_tabla("Maquinas")
        maquinas = df_maquinas["nombre_maquina"].tolist()

        maq = st.selectbox("Máquina", maquinas, key="maq2")
        nombre = st.text_input("Nombre")

        if st.button("Guardar maquinista"):
            insertar_tabla("Maquinistas", {
                "nombre": nombre,
                "maquina": maq
            })
            st.success("OK")

# ================= HISTORIAL =================
def historial():
    render_header("Historial")

    df = leer_tabla("ScrapRegistrado")

    if df.empty:
        st.info("Sin datos")
        return

    df["Fecha"] = pd.to_datetime(df["Fecha"])

    st.dataframe(df)

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "Descargar Excel",
        output,
        "scrap.xlsx"
    )

# ================= GRAFICOS =================
def graficos():
    render_header("Gráficos")

    df = leer_tabla("ScrapRegistrado")

    if df.empty:
        st.info("Sin datos")
        return

    df["Libras"] = pd.to_numeric(df["Libras"], errors="coerce").fillna(0)

    top_partes = df.groupby("Parte").size().sort_values(ascending=False).head(5)

    fig, ax = plt.subplots()
    ax.bar(top_partes.index, top_partes.values)
    plt.xticks(rotation=45)

    st.pyplot(fig)

# ================= ROUTER =================
if st.session_state.pantalla == "menu":
    menu()
elif st.session_state.pantalla == "escaneo":
    escaneo()
elif st.session_state.pantalla == "nuevo":
    nuevo()
elif st.session_state.pantalla == "historial":
    historial()
elif st.session_state.pantalla == "graficos":
    graficos()