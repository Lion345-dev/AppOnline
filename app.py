import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from google import genai

###################################
tokenGenAI = "AIzaSyALEvLCwPBjrcdh0--L8zulv5ObyDxx040"
client = genai.Client(api_key=tokenGenAI)
###################################

# Configuración de la página
st.set_page_config(
    page_title="Análisis Financiero Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        background-color: #121721;
    }
    .stTextInput>div>div>input {
        color: #ffffff;
        background-color: #1E2A3A;
        border: 1px solid #2E405B;
    }
    .css-1d391kg, .st-b7, .st-b8, .st-b9 {
        border-color: #2E405B !important;
    }
    .st-bb, .st-bc, .st-bd {
        background-color: #121721 !important;
    }
    .stMetric {
        background-color: #1E2A3A;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #00C4CC;
    }
    .st-eb {
        background-color: #1E2A3A;
    }
    .st-c0 {
        color: #FFFFFF !important;
    }
    .stock-card {
        background: linear-gradient(90deg, #1E2A3A 0%, #2E405B 100%);
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #5E81AC;
    }
    .section-title {
        background: #1E2A3A;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 4px solid #00C4CC;
    }
    .news-card {
        background: #2E405B;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #D08770;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialización de session state
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar mejorado
with st.sidebar:
    st.markdown("""
        <div class="section-title">
            <h3 style="color: #E5E9F0; margin:0;">🔍 Búsqueda</h3>
        </div>
        """, unsafe_allow_html=True)
    
    symbol = st.text_input(
        "Ingresa el símbolo de la acción:",
        placeholder="Ej: AAPL, MSFT, TSLA",
        key="search_input",
        label_visibility="collapsed"
    )
    
    st.markdown("""
        <div class="section-title" style="border-left-color: #5E81AC;">
            <h3 style="color: #E5E9F0; margin:0;">⭐ Favoritos</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Mostrar favoritos con claves únicas
    for i, fav in enumerate(st.session_state.favorites):
        if st.button(
            fav,
            key=f"fav_{i}_{fav}",
            help=f"Cargar {fav}",
            use_container_width=True
        ):
            st.session_state.search_input = fav
            st.experimental_rerun()
    
    st.markdown("""
        <div class="section-title" style="border-left-color: #BF616A;">
            <h3 style="color: #E5E9F0; margin:0;">🕒 Historial</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Mostrar historial con claves únicas (últimos 5, más reciente primero)
    for i, hist in enumerate(reversed(st.session_state.history[-5:])):
        if st.button(
            hist,
            key=f"hist_{i}_{hist}",
            help=f"Cargar {hist}",
            use_container_width=True
        ):
            st.session_state.search_input = hist
            st.experimental_rerun()

# Contenido principal
symbol = st.session_state.get('search_input', '')

if symbol:
    try:
        start_time = time.time()
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Validación de símbolo
        if not info:
            st.error("⚠️ Símbolo no válido. Intenta con otro.")
        else:
            # Actualizar historial (sin duplicados)
            if symbol not in st.session_state.history:
                st.session_state.history.append(symbol)
            
            # Obtener 5 años de datos
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            history = stock.history(start=start_date, end=end_date)
            
            # Mostrar encabezado de la compañía
            st.markdown(f"""
                <div class="stock-card">
                    <h2 style="color: #E5E9F0; margin:0;">{info.get('longName', symbol)}</h2>
                    <p style="color: #D8DEE9; margin:0;">{info.get('sector', '')} | {info.get('industry', '')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Descripción de la empresa con GenAI
            with st.expander("📌 Descripción de la Empresa", expanded=True):
                if 'longBusinessSummary' in info:
                    prompt = f"Traduce al español y resume en 3 párrafos máximo: {info['longBusinessSummary']}"
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    st.write(response.text)
                else:
                    st.warning("Descripción no disponible")
            
            # --- Gráfico interactivo de 5 años ---
            st.markdown("""
                <div class="section-title">
                    <h3 style="color: #E5E9F0; margin:0;">📈 Historial de 5 Años</h3>
                </div>
                """, unsafe_allow_html=True)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Línea de precio principal
            fig.add_trace(
                go.Scatter(
                    x=history.index,
                    y=history['Close'],
                    name="Precio",
                    line=dict(color='#00C4CC', width=2),
                    hovertemplate='<b>Fecha</b>: %{x|%d-%m-%Y}<br><b>Precio</b>: $%{y:.2f}<extra></extra>'
                ),
                secondary_y=False
            )
            
            # Media móvil de 200 días
            fig.add_trace(
                go.Scatter(
                    x=history.index,
                    y=history['Close'].rolling(200).mean(),
                    name="MA 200",
                    line=dict(color='#EBCB8B', width=1.5, dash='dot'),
                    hovertemplate='MA 200: $%{y:.2f}<extra></extra>'
                ),
                secondary_y=False
            )
            
            # Volumen
            fig.add_trace(
                go.Bar(
                    x=history.index,
                    y=history['Volume'],
                    name="Volumen",
                    marker_color='#4C566A',
                    opacity=0.6,
                    hovertemplate='<b>Volumen</b>: %{y:,}<extra></extra>'
                ),
                secondary_y=True
            )
            
            # Diseño del gráfico
            fig.update_layout(
                height=600,
                template='plotly_dark',
                plot_bgcolor='#121721',
                paper_bgcolor='#121721',
                font=dict(color='#E5E9F0'),
                hovermode='x unified',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                margin=dict(l=50, r=50, b=50, t=50, pad=10),
                xaxis=dict(
                    rangeslider=dict(visible=False),
                    type='date',
                    gridcolor='#2E405B',
                    showspikes=True,
                    spikethickness=1
                ),
                yaxis=dict(
                    title='Precio (USD)',
                    gridcolor='#2E405B',
                    showspikes=True
                ),
                yaxis2=dict(
                    title='Volumen',
                    showgrid=False,
                    side='right'
                )
            )
            
            # Selector de rango
            fig.update_xaxes(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="5A")
                    ]),
                    bgcolor='#1E2A3A',
                    activecolor='#4C566A',
                    font=dict(color='#E5E9F0')
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
            
            # --- Sección de métricas clave ---
            st.markdown("""
                <div class="section-title" style="border-left-color: #5E81AC;">
                    <h3 style="color: #E5E9F0; margin:0;">📊 Métricas Clave</h3>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Precio Actual",
                    value=f"${info.get('currentPrice', 'N/A'):,.2f}",
                    delta=f"{info.get('regularMarketChangePercent', 'N/A'):,.2f}%" if 'regularMarketChangePercent' in info else None
                )
                st.metric("Mín. 52 Sem", f"${info.get('fiftyTwoWeekLow', 'N/A'):,.2f}")
                
            with col2:
                st.metric("Capitalización", f"${info.get('marketCap', 'N/A'):,.0f}")
                st.metric("Ratio P/E", f"{info.get('trailingPE', 'N/A'):,.1f}")
                
            with col3:
                st.metric("Máx. 52 Sem", f"${info.get('fiftyTwoWeekHigh', 'N/A'):,.2f}")
                st.metric("Beta", f"{info.get('beta', 'N/A'):,.2f}")
                
            with col4:
                st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                st.metric("Vol. Promedio", f"{info.get('averageVolume', 'N/A'):,}")
            
            # --- Noticias recientes ---
            st.markdown("""
                <div class="section-title" style="border-left-color: #BF616A;">
                    <h3 style="color: #E5E9F0; margin:0;">📰 Noticias Recientes</h3>
                </div>
                """, unsafe_allow_html=True)
            
            news = stock.news
            for item in news[:5]:
                publish_time = datetime.fromtimestamp(item['providerPublishTime']).strftime('%d/%m/%Y %H:%M') if 'providerPublishTime' in item else ''
                st.markdown(f"""
                    <div class="news-card">
                        <h4 style="color: #E5E9F0; margin:0 0 10px 0;">{item.get('title', 'Título no disponible')}</h4>
                        <p style="color: #D8DEE9; margin:0; font-size: 0.9em;">
                            {item.get('publisher', 'Fuente desconocida')} - {publish_time}
                        </p>
                        <a href="{item.get('link', '#')}" target="_blank" style="color: #5E81AC; text-decoration: none;">Leer más →</a>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Botón para agregar a favoritos
            col_fav, _ = st.columns([1, 3])
            with col_fav:
                if st.button("⭐ Agregar a Favoritos", key="add_fav"):
                    if symbol not in st.session_state.favorites:
                        st.session_state.favorites.append(symbol)
                        st.success(f"{symbol} agregado a favoritos!")
                        st.experimental_rerun()
                    else:
                        st.warning(f"{symbol} ya está en tus favoritos")
            
    except Exception as e:
        st.error(f"⛔ Error al obtener los datos: {str(e)}")

# Mensaje de ayuda inicial
else:
    st.markdown("""
        <div style="background: #1E2A3A;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-top: 50px;
                    border-left: 5px solid #5E81AC;">
            <h3 style="color: #E5E9F0;">🔎 Busca un símbolo para comenzar</h3>
            <p style="color: #D8DEE9;">Ejemplos: AAPL (Apple), MSFT (Microsoft), TSLA (Tesla)</p>
        </div>
        """, unsafe_allow_html=True)