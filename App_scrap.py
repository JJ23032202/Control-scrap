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
        "modo_scan": False,
        "causa_qr": "",
        "maquina_sel": "-- Seleccione --",
        "parte_sel": "-- Seleccione --",
        "plan_sel": "-- Seleccione --",
        "otro_texto": "",
        "libras": "",
        "firma_sel": "-- Seleccione --",
        "fecha": datetime.now().date(),
        "abrir_teclado": False,
        "limpiar_form": False
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

    if st.session_state.limpiar_form:
        st.session_state.causa_qr = ""
        st.session_state.maquina_sel = "-- Seleccione --"
        st.session_state.parte_sel = "-- Seleccione --"
        st.session_state.plan_sel = "-- Seleccione --"
        st.session_state.otro_texto = ""
        st.session_state.libras = ""
        st.session_state.firma_sel = "-- Seleccione --"
        st.session_state.fecha = datetime.now().date()
        st.session_state.limpiar_form = False

    # ================= ESCANEAR QR =================
    if st.button("🔍 Escanear", use_container_width=True):
        st.session_state.modo_scan = True
        st.session_state.causa_qr = ""
        st.session_state._qr_tmp = ""

    if st.session_state.modo_scan:
        qr = st.text_input(
            "",
            key="_qr_tmp",
            placeholder="Escanee el QR…",
            label_visibility="collapsed"
        )
        if qr:
            st.session_state.causa_qr = qr.strip()
            st.session_state.modo_scan = False
            st.rerun()

    st.text_input("Causa", st.session_state.causa_qr, disabled=True)
    st.divider()

    # ================= CARGA DE TABLAS =================
    df_maquinas = leer_tabla("maquinas")
    df_partes = leer_tabla("numeros_parte")
    df_planes = leer_tabla("planes_accion")
    df_maquinistas = leer_tabla("maquinistas")

    # ===== MAPEO nombre -> id =====
    map_maquinas = dict(
        zip(df_maquinas["nombre_maquina"], df_maquinas["id"])
    )

    # ================= FILA 3 =================
    col1, col2 = st.columns(2)

    with col1:
        maquinas = ["-- Seleccione --"] + df_maquinas["nombre_maquina"].dropna().tolist()
        st.selectbox("Máquina", maquinas, key="maquina_sel")

    maquina_id = map_maquinas.get(st.session_state.maquina_sel)

    with col2:
        partes = ["-- Seleccione --"]
        if maquina_id is not None:
            partes += df_partes[
                df_partes["maquina"] == maquina_id
            ]["numero_parte"].dropna().tolist()

        st.selectbox("Número de parte", partes, key="parte_sel")

    # ================= FILA 4 =================
    col3, col4 = st.columns(2)

    with col3:
        planes = ["-- Seleccione --"] + df_planes["plan"].dropna().tolist()
        st.selectbox("Plan de acción", planes, key="plan_sel")

        st.text_input(
            "Colocar otro",
            key="otro_texto",
            disabled=st.session_state.plan_sel.upper() != "OTRO"
        )

    with col4:
        st.text_input("Libras", key="libras")

    # ================= FILA 5 =================
    col5, col6 = st.columns(2)

    with col5:
        firmas = ["-- Seleccione --"]
        if maquina_id is not None:
            firmas += df_maquinistas[
                df_maquinistas["maquina"] == maquina_id
            ]["nombre"].dropna().tolist()

        st.selectbox("Maquinista", firmas, key="firma_sel")

    with col6:
        st.date_input("Fecha", key="fecha")

    st.divider()

    # ================= GUARDAR =================
    if st.button("Guardar", use_container_width=True):

        causa_final = (
            st.session_state.otro_texto
            if st.session_state.plan_sel.upper() == "OTRO"
            else st.session_state.causa_qr
        )

        if (
            causa_final == ""
            or st.session_state.maquina_sel == "-- Seleccione --"
            or st.session_state.parte_sel == "-- Seleccione --"
            or st.session_state.plan_sel == "-- Seleccione --"
            or st.session_state.firma_sel == "-- Seleccione --"
            or st.session_state.libras == ""
        ):
            st.error("❌ Faltan datos obligatorios")
            return

        insertar_tabla("scrap_registrado", {
            "fecha": str(st.session_state.fecha),
            "maquina": maquina_id,
            "parte": st.session_state.parte_sel,
            "causa": causa_final,
            "plan_accion": st.session_state.plan_sel,
            "libras": float(st.session_state.libras),
            "firma": st.session_state.firma_sel,
        })

        st.success("✅ Scrap guardado correctamente")

        st.session_state.limpiar_form = True
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



if "pantalla" not in st.session_state:
    st.session_state.pantalla = "menu"

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