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

# ================= SESSION =================
def init_state():
    defaults = {
        "pantalla": "menu",
        "parte": "",
        "maquina": "",
        "libras": "",
        "fecha": datetime.now().date(),
        "modo_scan": False,
        "qr_buffer": "",
        "causa_qr": "",

    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ================= HELPERS =================
def leer_tabla(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        if not res.data:
            return pd.DataFrame()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error en {tabla}: {e}")
        return pd.DataFrame()

def insertar_tabla(tabla, data):
    try:
        supabase.table(tabla).insert(data).execute()
    except Exception as e:
        st.error(f"Error insertando en {tabla}: {e}")

# ================= HEADER =================

def render_header(titulo):
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        if st.button("⬅️"):
            st.session_state.pantalla = "menu"
            st.rerun()

    with col2:
        st.markdown(
            f"<h2 style='text-align:center; color:#E36B2C;'>{titulo}</h2>",
            unsafe_allow_html=True
        )

    with col3:
        st.image(
            "https://hdscbglzatctcjzecean.supabase.co/storage/v1/object/public/logo_versigent/logo_versigent.png",
            width=140
        )



# ================= MENU =================
def menu():
    st.title("Control de Scrap")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("📷 Escaneo"):
            st.session_state.pantalla = "escaneo"
        if st.button("➕ Nuevo"):
            st.session_state.pantalla = "nuevo"

    with c2:
        if st.button("📊 Historial"):
            st.session_state.pantalla = "historial"
        if st.button("📈 Gráficos"):
            st.session_state.pantalla = "graficos"

# ================= ESCANEO =================

def escaneo():
    render_header("Escaneo de Scrap")

    # ================= FILA 1: ESCANEAR =================
    if st.button("🔍 Escanear", use_container_width=True):
        st.session_state.modo_scan = True
        st.session_state.causa_qr = ""

    # ===== INPUT OCULTO PARA SCANNER ZEBRA =====
    if st.session_state.modo_scan:
        qr = st.text_input("QR", key="qr_input", label_visibility="collapsed")

        if qr:
            st.session_state.causa_qr = qr.strip()
            st.session_state.modo_scan = False

    # ================= FILA 2: CAUSA =================
    st.text_input(
        "Causa",
        value=st.session_state.causa_qr,
        disabled=True
    )

    st.divider()

    # ================= CARGAR CATÁLOGOS =================
    df_maquinas = leer_tabla("maquinas")
    df_partes = leer_tabla("numeros_parte")
    df_planes = leer_tabla("planes_accion")
    df_maquinistas = leer_tabla("maquinistas")

    # ================= FILA 3 =================
    col1, col2 = st.columns(2)

    with col1:
        maquinas = df_maquinas["nombre_maquina"].dropna().tolist()
        maquina = st.selectbox("Seleccionar Máquina", maquinas)

    with col2:
        partes = []
        if maquina:
            partes = (
                df_partes[df_partes["maquina"] == maquina]["numero_parte"]
                .dropna()
                .tolist()
            )
        parte = st.selectbox("Seleccionar Número de Parte", partes)

    # ================= FILA 4 =================
    col3, col4 = st.columns(2)

    with col3:
        planes = df_planes["plan"].dropna().tolist()
        plan = st.selectbox("Seleccionar Plan de acción", planes)

        causa_manual = st.text_input("Colocar otro (manual)")

    with col4:
        st.text_input(
            "Colocar Libras",
            value=st.session_state.libras,
            disabled=True
        )

        if st.button("⌨️"):
            # Aquí entra TU teclado numérico existente
            st.session_state.libras = ""

    # ================= FILA 5 =================
    col5, col6 = st.columns(2)

    with col5:
        firmas = []
        if maquina:
            firmas = (
                df_maquinistas[df_maquinistas["maquina"] == maquina]["nombre"]
                .dropna()
                .tolist()
            )
        firma = st.selectbox("Seleccionar maquinista", firmas)

    with col6:
        fecha = st.date_input("Seleccionar Fecha", st.session_state.fecha)

    st.divider()

    # ================= GUARDAR =================
    if st.button("Guardar", use_container_width=True):

        causa_final = causa_manual if causa_manual else st.session_state.causa_qr

        if not all([causa_final, maquina, parte, plan, st.session_state.libras]):
            st.error("❌ Faltan datos")
            return

        insertar_tabla("scrap_registrado", {
            "fecha": str(fecha),
            "maquina": maquina,
            "parte": parte,
            "causa": causa_final,
            "plan_accion": plan,
            "libras": float(st.session_state.libras),
            "firma": firma
        })

        st.success("✅ Scrap guardado correctamente")

        # ===== LIMPIAR TOdo =====
        st.session_state.modo_scan = False
        st.session_state.causa_qr = ""
        st.session_state.libras = ""
        st.session_state.fecha = datetime.now().date()

        st.rerun()

# ================= NUEVO =================
def nuevo():
    render_header("Nuevo")

    # -------- MAQUINA --------
    with st.expander("Máquina"):
        nombre = st.text_input("Nombre máquina")
        if st.button("Guardar máquina"):
            insertar_tabla("maquinas", {"nombre_maquina": nombre})
            st.success("OK")

    # -------- CAUSA --------
    with st.expander("Causa"):
        causa = st.text_input("Nueva causa")
        if st.button("Guardar causa"):
            insertar_tabla("causas", {"causa": causa})
            st.success("OK")

    # -------- PLAN --------
    with st.expander("Plan"):
        plan = st.text_input("Nuevo plan")
        if st.button("Guardar plan"):
            insertar_tabla("planes_accion", {"plan": plan})
            st.success("OK")

    # -------- PARTE --------
    with st.expander("Número de parte"):
        df_maquinas = leer_tabla("maquinas")
        maquinas = df_maquinas.get("nombre_maquina", pd.Series()).tolist()

        maq = st.selectbox("Máquina", maquinas)
        parte = st.text_input("Número")

        if st.button("Guardar parte"):
            insertar_tabla("numeros_parte", {
                "numero_parte": parte,
                "maquina": maq
            })
            st.success("OK")

    # -------- MAQUINISTA --------
    with st.expander("Maquinista"):
        df_maquinas = leer_tabla("maquinas")
        maquinas = df_maquinas.get("nombre_maquina", pd.Series()).tolist()

        maq = st.selectbox("Máquina", maquinas, key="maq2")
        nombre = st.text_input("Nombre")

        if st.button("Guardar maquinista"):
            insertar_tabla("maquinistas", {
                "nombre": nombre,
                "maquina": maq
            })
            st.success("OK")

# ================= HISTORIAL =================
def historial():
    render_header("Historial")

    df = leer_tabla("scrap_registrado")

    if df.empty:
        st.info("Sin registros")
        return

    st.dataframe(df)

    # descargar
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button("Descargar Excel", output, "historial.xlsx")

# ================= GRAFICOS =================
def graficos():
    render_header("Gráficos")

    df = leer_tabla("scrap_registrado")

    if df.empty:
        st.info("Sin datos")
        return

    df["libras"] = pd.to_numeric(df["libras"], errors="coerce").fillna(0)

    top = df.groupby("parte").size().sort_values(ascending=False).head(5)

    fig, ax = plt.subplots()
    ax.bar(top.index, top.values)
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