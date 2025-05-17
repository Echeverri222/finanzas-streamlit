import streamlit as st
st.set_page_config(page_title="Dashboard Financiero", layout="wide")

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px

# === CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ===

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(credentials)

SHEET_ID = "1W0gOUZFFJHvsP5f6aozHDWt519WEy1u2q8h0nImVCt8"
sheet = client.open_by_key(SHEET_ID).sheet1

# === FUNCIONES ===

def cargar_datos():
    """Carga los datos desde Google Sheets sin caché"""
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df["fecha"] = df["fecha"].astype(str).str.replace("'", "")
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["mes"] = df["fecha"].dt.to_period("M").astype(str)
    return df

def guardar_movimiento(fecha, nombre, importe, tipo):
    """Guarda un nuevo movimiento y retorna True si fue exitoso"""
    try:
        fecha_str = fecha.strftime("%Y-%m-%d")
        nueva_fila = [fecha_str, nombre, int(importe), tipo]
        next_row = len(sheet.get_all_values()) + 1
        sheet.append_row(nueva_fila)
        sheet.format(f"A{next_row}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al guardar el movimiento: {str(e)}")
        return False

def eliminar_movimiento(indice_sheet):
    try:
        sheet.delete_rows(indice_sheet + 2)  # +2 porque sheets empieza en 1 y tiene header
        st.cache_data.clear()
        st.success("✅ Movimiento eliminado correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"Error al eliminar el movimiento: {str(e)}")

# Cargar datos al inicio
df = cargar_datos()

fmt = lambda x: f"${x:,.0f}".replace(",", ".")

# === INTERFAZ PRINCIPAL ===

st.title("Finanzas Personales")

# === FILTROS PRINCIPALES ===
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    año = st.selectbox("Selecciona un año", sorted(df["fecha"].dt.year.unique()), index=0)
    df_filtrado = df[df["fecha"].dt.year == año]

with col2:    
    meses = ["Todos"] + sorted(df_filtrado["mes"].unique().tolist())
    mes_seleccionado = st.selectbox("Selecciona un mes", meses, index=0)
    
    if mes_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["mes"] == mes_seleccionado]

# Inicializar estados de sesión
if "mostrar_formulario" not in st.session_state:
    st.session_state["mostrar_formulario"] = False
if "mostrar_eliminar" not in st.session_state:
    st.session_state["mostrar_eliminar"] = False
if "confirmar_eliminar" not in st.session_state:
    st.session_state["confirmar_eliminar"] = False
if "indice_eliminar" not in st.session_state:
    st.session_state["indice_eliminar"] = None

# Crear pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen Gráfico", "📝 Gestión de Movimientos", "📋 Detalle Mensual", "📜 Lista de Movimientos"])

with tab1:
    # === RESUMEN GRÁFICO ===
    st.subheader("Resumen General")
    gastos_filtrados = df_filtrado[df_filtrado["tipo_movimiento"] != "Ingresos"]
    ingresos_filtrados = df_filtrado[df_filtrado["tipo_movimiento"] == "Ingresos"]

    total_gastos = gastos_filtrados["importe"].sum()
    total_ingresos = ingresos_filtrados["importe"].sum()
    balance = total_ingresos - total_gastos

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ingresos", fmt(total_ingresos))
    col2.metric("Total Gastos", fmt(total_gastos))
    col3.metric("Balance Neto", fmt(balance))

    # Gráficos de categorías
    st.subheader("Distribución de gastos por categoría")
    cat_summary = gastos_filtrados.groupby("tipo_movimiento")["importe"].sum().reset_index()
    cat_summary["porcentaje"] = 100 * cat_summary["importe"] / cat_summary["importe"].sum()
    cat_summary["importe_fmt"] = cat_summary["importe"].apply(fmt)

    # Definir colores específicos para cada categoría
    COLOR_MAP = {
        "Alimentacion": "#63B3ED",     # Azul claro
        "Transporte": "#38B2AC",       # Verde turquesa
        "Compras": "#F56565",          # Rojo
        "Gastos fijos": "#FBD38D",     # Rosa salmón
        "Ahorro": "#2B6CB0",           # Azul oscuro
        "Salidas": "#48BB78",          # Verde
        "Otros": "#D6BCFA"             # Morado claro
    }

    col1, col2 = st.columns(2)
    # Gráfico de torta
    fig1 = px.pie(cat_summary, names="tipo_movimiento", values="porcentaje", 
                title="Distribución por categoría",
                color="tipo_movimiento",
                color_discrete_map=COLOR_MAP)
    fig1.update_traces(textinfo="percent")

    # Gráfico de barras horizontales
    cat_summary_sorted = cat_summary.sort_values("importe", ascending=False)
    fig2 = px.bar(cat_summary_sorted, y="tipo_movimiento", x="importe", text="importe_fmt",
                title="Gastos absolutos", orientation='h',
                color="tipo_movimiento",
                color_discrete_map=COLOR_MAP)
    fig2.update_layout(showlegend=False)

    col1.plotly_chart(fig1, use_container_width=True)
    col2.plotly_chart(fig2, use_container_width=True)

    # Evolución mensual
    st.subheader("Evolución mensual de gastos")
    evol = df[df["tipo_movimiento"] != "Ingresos"].groupby(["mes", "tipo_movimiento"])["importe"].sum().reset_index()
    fig_line = px.line(evol, x="mes", y="importe", color="tipo_movimiento", markers=True,
                      color_discrete_map=COLOR_MAP)
    fig_line.update_layout(yaxis_tickformat=",", yaxis_tickprefix="$ ")
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    # === GESTIÓN DE MOVIMIENTOS ===
    st.subheader("Gestión de Movimientos")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Añadir Nuevo Movimiento"):
            st.session_state["mostrar_formulario"] = True
            st.session_state["mostrar_eliminar"] = False
    with col2:
        if st.button("➖ Eliminar Movimiento"):
            st.session_state["mostrar_eliminar"] = True
            st.session_state["mostrar_formulario"] = False

    # Formulario para añadir
    if st.session_state["mostrar_formulario"]:
        with st.form("formulario"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.today())
                importe = st.number_input("Importe", step=1000)
            with col2:
                nombre = st.text_input("Nombre del movimiento")
                tipo = st.selectbox("Tipo de movimiento", sorted(df["tipo_movimiento"].unique()) + ["Otro"])
            
            submit = st.form_submit_button("Agregar")
            if submit:
                if guardar_movimiento(fecha, nombre, importe, tipo):
                    st.success("Movimiento agregado correctamente.")
                    st.session_state["mostrar_formulario"] = False
                    df = cargar_datos()
                    st.rerun()

    # Interfaz para eliminar
    if st.session_state["mostrar_eliminar"]:
        st.markdown("### 🗑️ Eliminar Movimiento")
        busqueda = st.text_input("🔍 Buscar movimiento por nombre", "")
        
        df_eliminar = df.copy()
        df_eliminar["fecha"] = df_eliminar["fecha"].dt.strftime("%Y-%m-%d")
        df_eliminar["importe"] = df_eliminar["importe"].apply(fmt)
        
        if busqueda:
            df_eliminar = df_eliminar[df_eliminar["nombre"].str.contains(busqueda, case=False)]
        
        for idx, row in df_eliminar.iterrows():
            if st.session_state["confirmar_eliminar"] and st.session_state["indice_eliminar"] == idx:
                st.warning(f"⚠️ ¿Eliminar el movimiento '{row['nombre']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Sí", key=f"confirm_{idx}"):
                        eliminar_movimiento(idx)
                        st.session_state["mostrar_eliminar"] = False
                        st.session_state["confirmar_eliminar"] = False
                        st.session_state["indice_eliminar"] = None
                with col2:
                    if st.button("✗ No", key=f"cancel_{idx}"):
                        st.session_state["confirmar_eliminar"] = False
                        st.session_state["indice_eliminar"] = None
                        st.rerun()
            else:
                cols = st.columns([2, 3, 2, 2, 1])
                cols[0].write(row["fecha"])
                cols[1].write(row["nombre"])
                cols[2].write(row["importe"])
                cols[3].write(row["tipo_movimiento"])
                if cols[4].button("🗑️", key=f"del_{idx}"):
                    st.session_state["confirmar_eliminar"] = True
                    st.session_state["indice_eliminar"] = idx
                    st.rerun()
            st.markdown("---")
        
        if st.button("Cerrar"):
            st.session_state["mostrar_eliminar"] = False
            st.rerun()

with tab3:
    # === DETALLE MENSUAL ===
    st.subheader("Detalle por mes y categoría")
    
    # Crear pivot table incluyendo ingresos
    pivot = df_filtrado.groupby(["mes", "tipo_movimiento"])["importe"].sum().unstack(fill_value=0)
    # Reordenar columnas para que Ingresos sea la primera
    columnas = ["Ingresos"] + [col for col in pivot.columns if col != "Ingresos"]
    pivot = pivot[columnas]
    # Añadir columna de Total (Ingresos - Gastos)
    gastos_totales = pivot.drop("Ingresos", axis=1).sum(axis=1)
    pivot["Total"] = pivot["Ingresos"] - gastos_totales
    st.dataframe(pivot.style.format(fmt))

with tab4:
    # === LISTA DE MOVIMIENTOS ===
    st.subheader("Lista de Movimientos")
    
    col1, col2 = st.columns(2)
    with col1:
        categoria_filtro = st.multiselect(
            "Filtrar por categoría",
            options=sorted(df["tipo_movimiento"].unique().tolist())
        )
    with col2:
        mes_filtro = st.multiselect(
            "Filtrar por mes",
            options=sorted(df_filtrado["mes"].unique().tolist())
        )

    df_detalle = df_filtrado.copy()
    if categoria_filtro:
        df_detalle = df_detalle[df_detalle["tipo_movimiento"].isin(categoria_filtro)]
    if mes_filtro:
        df_detalle = df_detalle[df_detalle["mes"].isin(mes_filtro)]

    df_detalle = df_detalle.sort_values("fecha", ascending=False)
    df_detalle["fecha"] = df_detalle["fecha"].dt.strftime("%Y-%m-%d")
    df_detalle["importe"] = df_detalle["importe"].apply(fmt)

    st.dataframe(
        df_detalle[["fecha", "nombre", "importe", "tipo_movimiento"]],
        column_config={
            "fecha": "Fecha",
            "nombre": "Descripción",
            "importe": "Importe",
            "tipo_movimiento": "Categoría"
        },
        hide_index=True
    )