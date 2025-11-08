import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from google.oauth2 import service_account
from google.analytics.data_v1beta.types import GetMetadataRequest
import json

# User config
CREDENTIALS_INFO = st.secrets["ga4"]["key"]
CREDENTIALS_DICT = json.loads(CREDENTIALS_INFO)
CREDENTIALS = service_account.Credentials.from_service_account_info(CREDENTIALS_DICT)
CLIENT = BetaAnalyticsDataClient(credentials=CREDENTIALS)
PROPERTY_ID = "480682703"
HOTEL_NAME = "Buen Valle"
START_DATE = "2025-10-01"
END_DATE = "2025-10-31"


# Page config
st.set_page_config(
    page_title=f"Analytics - {HOTEL_NAME}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Data extraction function
def ga4_to_dataframe(dimensions, metrics, start_date, end_date):
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )

    response = CLIENT.run_report(request)

    rows = []
    for row in response.rows:
        row_data = {}
        for i, dim in enumerate(dimensions):
            row_data[dim] = row.dimension_values[i].value
        for i, metric in enumerate(metrics):
            row_data[metric] = float(row.metric_values[i].value)
        rows.append(row_data)
    
    return pd.DataFrame(rows)

# * 1. Performance df
performance_df = ga4_to_dataframe(
    dimensions=["date"],
    metrics=[
        "activeUsers", "newUsers", "sessions", "engagedSessions",
        "engagementRate", "bounceRate", "averageSessionDuration", 
        "screenPageViewsPerSession", "eventCount", "userEngagementDuration"
    ],
    start_date=START_DATE,
    end_date=END_DATE
)

performance_df.rename(columns={
    # "date": "fecha",
    "activeUsers": "usuariosActivos",
    "newUsers": "usuariosNuevos",
    "sessions": "sesiones",
    "engagedSessions": "sesionesComprometidas",
    "engagementRate": "tasaCompromiso",
    "bounceRate": "tasaRebote",
    "averageSessionDuration": "duracionPromedioSesion",
    "screenPageViewsPerSession": "vistasPaginaPorSesion",
    "eventCount": "conteoEventos",
    "userEngagementDuration": "duracionCompromisoUsuario"
}, inplace=True)

performance_df.sort_values(by="date", inplace=True)

# * 2. Channels df
channels_df = ga4_to_dataframe(
    dimensions=["sessionSource", "sessionMedium"],
    metrics=["sessions","engagedSessions","engagementRate","bounceRate","averageSessionDuration"],
    start_date=START_DATE,
    end_date=END_DATE
)

channels_df.drop(0, inplace=True)

channels_df.rename(columns={
    # "sessionSource": "fuenteSesion",
    # "sessionMedium": "medioSesion",
    "sessions": "sesiones",
    "engagedSessions": "sesionesComprometidas",
    "engagementRate": "tasaCompromiso",
    "bounceRate": "tasaRebote",
    "averageSessionDuration": "duracionPromedioSesion"
}, inplace=True)

channels_df['canal'] = channels_df['sessionSource'] + " / " + channels_df['sessionMedium']

# * 3. Pages df
pages_df = ga4_to_dataframe(
    dimensions=["pageTitle","pagePath"],
    metrics=["screenPageViews","userEngagementDuration","eventCount","bounceRate"],
    start_date=START_DATE,
    end_date=END_DATE
)

pages_df.rename(columns={
    # "pageTitle": "tituloPagina",
    # "pagePath": "rutaPagina",
    "screenPageViews": "vistasPagina",
    "userEngagementDuration": "duracionCompromisoUsuario",
    "eventCount": "conteoEventos",
    "bounceRate": "tasaRebote"
}, inplace=True)

pages_df.sort_values("vistasPagina", ascending=False).head(5)

# * 4. Events df
events_df = ga4_to_dataframe(
    dimensions=["eventName"],
    metrics=["eventCount","totalUsers"],
    start_date=START_DATE,
    end_date=END_DATE
)

events_df.rename(columns={
    # "eventName": "nombreEvento",
    "eventCount": "conteoEventos",
    "totalUsers": "usuariosTotales"
}, inplace=True)

events_df['eventName'] = events_df['eventName'].replace('form_submit', 'buscar_disponibilidad')

events_df.sort_values("conteoEventos", ascending=False)

# * 5. Devices df
devices_df = ga4_to_dataframe(
    dimensions=["deviceCategory"],
    metrics=["sessions","engagedSessions","engagementRate","bounceRate","eventCount"],
    start_date=START_DATE,
    end_date=END_DATE
)

devices_df.rename(columns={
    # "deviceCategory": "dispositivo",
    "sessions": "sesiones", 
    "engagedSessions": "sesionesComprometidas",
    "engagementRate": "tasaCompromiso",
    "bounceRate": "tasaRebote",
    "eventCount": "conteoEventos"
}, inplace=True)

# * Streamlit app
st.title(f"🏨 Analytics - {HOTEL_NAME}")
st.markdown("---")

# * Page info
st.subheader("Configuración de Google Analytics 4")
st.info(f"ID del hotel: {PROPERTY_ID}")
st.subheader("Datos utilizados")
if performance_df is not None:
    st.write(f"📅 Periodo: {START_DATE} a {END_DATE}")
    st.write(f"👥 Usuarios totales: {performance_df['usuariosActivos'].sum():,}")
    st.write(f"🔄 Sesiones totales: {performance_df['sesiones'].sum():,}")
st.markdown(
    "**Dashboard conectado a Google Analytics 4** | "
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

# * Mostrar glosario expandible
st.markdown("---")
st.subheader("Glosario de métricas")
with st.expander("Click para expandir"):
    st.markdown("""

    #### Métricas principales de performance

    - **Usuarios activos**: Número total de usuarios que interactuaron con el sitio web  
    - **Usuarios nuevos**: Usuarios que visitaron el sitio por primera vez  
    - **Sesiones**: Periodos de interacción continua en el sitio web  
    - **Sesiones comprometidas**: Sesiones de calidad (duración >10 segundos o múltiples páginas)  
    - **Tasa de compromiso**: % de sesiones de calidad (sesiones comprometidas / sesiones totales)
    - **Tasa de rebote**: % de sesiones de baja calidad (duración <10 segundos, se calcula como 1 - tasa de compromiso) 
    - **Duración promedio de sesión**: Tiempo promedio que los usuarios permanecen en el sitio  
    - **Vistas de página por sesión**: Número promedio de páginas vistas por sesión  

    #### Términos de canales
    - **Fuente/Medio**: Origen y método del tráfico (ej: Google / orgánico)  
    - **Canal**: Combinación de fuente y medio   

    #### Interpretación rápida
    **Métricas positivas** (más alto = mejor):  
    - Tasa de compromiso, Duración de sesión, Vistas por sesión  

    **Métricas negativas** (más bajo = mejor):  
    - Tasa de rebote
    """)

st.markdown("---")

# * 1. Performance section
st.header("Performance general")

if performance_df is not None:
    # KPIs 
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_users = performance_df['usuariosActivos'].sum()
        st.metric(
            label="Usuarios totales", 
            value=f"{total_users:,}"
        )

    with col2:
        avg_engagement = performance_df['tasaCompromiso'].mean()
        st.metric(
            label="Tasa de compromiso", 
            value=f"{avg_engagement:.1%}"
        )
    
    with col3:
        avg_bounce = performance_df['tasaRebote'].mean()
        st.metric(
            label="Tasa de rebote", 
            value=f"{avg_bounce:.1%}"
        )

    with col4:
        avg_duration = performance_df['duracionPromedioSesion'].mean()
        minutes = int(avg_duration // 60)
        seconds = int(avg_duration % 60)
        st.metric(
            label="Duración promedio", 
            value=f"{minutes}:{seconds:02d} min"
        )

    with col5:
        avg_views = performance_df['vistasPaginaPorSesion'].mean()
        st.metric(
            label="Páginas/Sesión", 
            value=f"{avg_views:.1f}"
        )

    # Chart
    st.subheader("Tendencias de tráfico")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=performance_df['date'],
        y=performance_df['usuariosActivos'],
        name='Usuarios activos',
        line=dict(color='#1f77b4', width=3)
    ))
    fig_trend.add_trace(go.Scatter(
        x=performance_df['date'],
        y=performance_df['sesiones'],
        name='Sesiones',
        line=dict(color='#ff7f0e', width=3)
    ))
    fig_trend.update_layout(
        height=300,
        xaxis_title="Fecha",
        yaxis_title="Cantidad",
        template="plotly_white"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("No hay datos de performance disponibles")

# * 2. Channel section
st.header("Comportamiento por canal")

if channels_df is not None:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Performance por canal")
        
        fig_canal = px.bar(
            channels_df.head(8),
            x='canal',
            y='sesiones',
            color='tasaCompromiso',
            color_continuous_scale='Viridis',
            title='Sesiones y engagement por canal'
        )
        fig_canal.update_layout(height=400)
        st.plotly_chart(fig_canal, use_container_width=True)

    with col2:
        st.subheader("Métricas detalladas")
        
        canal_display = channels_df.copy()
        canal_display['tasaCompromiso'] = canal_display['tasaCompromiso'].apply(lambda x: f"{x:.1%}")
        canal_display['tasaRebote'] = canal_display['tasaRebote'].apply(lambda x: f"{x:.1%}")
        canal_display['duracionPromedioSesion'] = canal_display['duracionPromedioSesion'].apply(lambda x: f"{int(x//60)}:{int(x%60):02d}")
        
        st.dataframe(
            canal_display,
            column_config={
                "canal": "Canal",
                "sessions": "Sesiones",
                "engagementRate": "Compromiso",
                "bounceRate": "Rebote",
                "averageSessionDuration": "Duración"
            },
            use_container_width=True
        )
else:
    st.warning("No hay datos de canales disponibles")

# * 3. Pages section 
st.header("Análisis de páginas")

if pages_df is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top páginas visitadas")
        
        fig_paginas = px.bar(
            pages_df.head(6),
            x='vistasPagina',
            y='pagePath',
            orientation='h',
            color='duracionCompromisoUsuario',
            color_continuous_scale='Blues',
            title='Vistas por página',
            text='vistasPagina'
        )
    
        fig_paginas.update_traces(
            texttemplate='%{text:.0f}',  
            textposition='outside'      
        )
        
        fig_paginas.update_layout(
            height=400,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        
        st.plotly_chart(fig_paginas, use_container_width=True)

    with col2:
        st.subheader("Tiempo vs Interacciones")
        
        if len(pages_df) > 1:
            fig_scatter = px.scatter(
                pages_df,
                x='duracionCompromisoUsuario',
                y='conteoEventos',
                size='vistasPagina',
                color='pagePath',
                title='Relación: Tiempo vs Interacciones',
                size_max=40,
                text='conteoEventos'  # 👈 Muestra el valor del eje Y, puedes cambiarlo por 'vistasPagina' si prefieres
            )
            
            # Ajustes de estilo del texto
            fig_scatter.update_traces(
                textposition='top center',  # posición del texto sobre los puntos
                textfont=dict(size=10),
                hovertemplate=(
                    "<b>%{text}</b><br>" +
                    "Duración: %{x}<br>" +
                    "Interacciones: %{y}<br>" +
                    "Vistas: %{marker.size}"
                )
            )
            
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No hay suficientes datos para el gráfico de dispersión")
else:
    st.warning("No hay datos de páginas disponibles")

# * 4. Events section
st.header("Eventos y conversiones")

if events_df is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Eventos más frecuentes")
        
        fig_eventos = px.bar(
            events_df.head(10),
            x='conteoEventos',
            y='eventName',
            orientation='h',
            color='conteoEventos',
            color_continuous_scale='Greens',
            title='Top eventos'
        )
        fig_eventos.update_layout(height=400)
        st.plotly_chart(fig_eventos, use_container_width=True)

    with col2:
        st.subheader("Usuarios por evento")
        
        fig_usuarios_eventos = px.pie(
            events_df.head(6),
            values='usuariosTotales',
            names='eventName',
            title='Distribución de usuarios por evento'
        )
        fig_usuarios_eventos.update_layout(height=400)
        st.plotly_chart(fig_usuarios_eventos, use_container_width=True)
else:
    st.warning("No hay datos de eventos disponibles")

# Devices section
st.header("Análisis por dispositivo")

if devices_df is not None:
    # col1, col2 = st.columns(2)
    col1 = st.columns(1)[0]

    with col1:
        st.subheader("Distribución por dispositivo")
        
        fig_pie = px.pie(
            devices_df,
            values='sesiones',
            names='deviceCategory',
            title='Sesiones por dispositivo',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    # with col2:
    #     st.subheader("Performance comparativa")
        
    #     # Radar chart
    #     fig_radar = go.Figure()
        
    #     for _, row in devices_df.iterrows():
    #         fig_radar.add_trace(go.Scatterpolar(
    #             r=[row['tasaCompromiso'], 1-row['tasaRebote'], row['sesiones']/max(devices_df['sesiones'])],
    #             theta=['Compromiso', 'Retención', 'Sesiones'],
    #             fill='toself',
    #             name=row['deviceCategory']
    #         ))
        
    #     fig_radar.update_layout(
    #         polar=dict(
    #             radialaxis=dict(visible=True, range=[0, 1])
    #         ),
    #         showlegend=True,
    #         height=400,
    #         title="Comparativa de métricas por dispositivo"
    #     )
    #     st.plotly_chart(fig_radar, use_container_width=True)
else:
    st.warning("No hay datos de dispositivos disponibles")

