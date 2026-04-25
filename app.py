import streamlit as st
import pandas as pd
import requests

# Configuração de Página para Celular
st.set_page_config(page_title="Garimpeiro de Ofertas", page_icon="💰")

# Chave que você copiou
API_KEY = "f8cfed50639a72002e65c721b3db1d5e57f91ea6246c1f69e75495145a1f5b13"

# Estilo Visual Profissional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div.stButton > button:first-child {
        height: 3.5em; width: 100%; border-radius: 12px;
        font-size: 20px; font-weight: bold; background-color: #2E7D32; color: white;
    }
    .card {
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Garimpeiro de Ofertas")
st.write("Pesquisa global em tempo real (Farmácias e Lojas)")

# --- FUNÇÃO DE BUSCA VIA SERPAPI ---
def buscar_ofertas(produto):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": produto,
        "hl": "pt-br",
        "gl": "br",
        "api_key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        return data.get("shopping_results", [])
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return []

# --- INTERFACE ---
query = st.text_input("O que você busca?", placeholder="Ex: Fralda Pampers G")

if st.button("🔍 VASCULHAR INTERNET"):
    if query:
        with st.spinner('Acessando servidores...'):
            resultados = buscar_ofertas(query)
            
            if resultados:
                # O primeiro resultado da SerpApi costuma ser o melhor preço
                top = resultados[0]
                
                st.subheader("🏆 Melhor Opção Encontrada")
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <img src="{top.get('thumbnail')}" style="width:100px; float:right;">
                        <h2 style="color:#2E7D32;">{top.get('price')}</h2>
                        <p><b>Loja:</b> {top.get('source')}</p>
                        <p style="font-size:14px;">{top.get('title')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button("🛒 ABRIR NA LOJA", top.get('link'))

                st.write("---")
                st.write("📊 **Outras Lojas:**")
                
                # Lista as próximas 4 ofertas
                for item in resultados[1:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{item.get('source')}**")
                        st.caption(item.get('title'))
                    with col2:
                        st.write(f"**{item.get('price')}**")
                    st.write(f"[Link da oferta]({item.get('link')})")
                    st.divider()

                # --- ÁREA DO SEU LUCRO ---
                st.warning("🔔 **MONITORAMENTO AUTOMÁTICO**")
                st.write("Quer que eu te avise no WhatsApp se esse preço cair?")
                with st.expander("ATIVAR ALERTA (R$ 10,00)"):
                    st.write("1. Envie o PIX para sua chave.")
                    zap = st.text_input("Seu WhatsApp:")
                    if st.button("ATIVAR VIGILÂNCIA"):
                        st.success("Tudo certo! Robô ativado para este produto.")
                        st.balloons()
            else:
                st.error("Nenhum produto encontrado. Tente ser mais específico.")
    else:
        st.warning("Digite algo para buscar.")

st.caption("Arquiteto de Dados Renato - 2026")
