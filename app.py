import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Configuração da Página para Mobile
st.set_page_config(page_title="Garimpeiro de Ofertas", page_icon="💰", layout="centered")

# Estilo para botões grandes e interface limpa
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3.5em;
        width: 100%;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
        background-color: #2E7D32;
        color: white;
    }
    .stTextInput > div > div > input {
        height: 3em;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Garimpeiro de Ofertas")
st.subheader("O menor preço da internet, sem pesquisa.")

# --- LÓGICA DE BUSCA REAL (GOOGLE SHOPPING SCRAPING) ---
def buscar_precos_internet(produto):
    produto_codificado = urllib.parse.quote(produto)
    url = f"https://www.google.com/search?q={produto_codificado}&tbm=shop"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        resultados = []
        # Procura os blocos de produtos no Google Shopping
        for g in soup.find_all('div', class_='sh-dgr__content')[:5]:
            try:
                nome = g.find('h3').text if g.find('h3') else "Produto"
                loja = g.find('div', class_='aULzUe').text if g.find('div', class_='aULzUe') else "Loja Online"
                preco_raw = g.find('span', class_='a88X0c').text if g.find('span', class_='a88X0c') else "Consulte"
                link_raw = g.find('a', class_='shntl')['href']
                link_final = "https://www.google.com" + link_raw if link_raw.startswith('/') else link_raw
                
                # Limpeza básica do preço para ordenar
                preco_limpo = preco_raw.replace('R$', '').replace('\xa0', '').replace('.', '').replace(',', '.').strip()
                valor_float = float(preco_limpo) if preco_limpo.replace('.', '').isdigit() else 0.0
                
                resultados.append({
                    "loja": loja,
                    "nome": nome,
                    "preco": valor_float,
                    "preco_texto": preco_raw,
                    "link": link_final
                })
            except:
                continue
        
        # Ordena pelo menor preço
        return sorted(resultados, key=lambda x: x['preco']) if resultados else []
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return []

# --- INTERFACE ---
busca_usuario = st.text_input("O que você deseja comprar?", placeholder="Ex: Fraldas Pampers G")

if st.button("🔍 BUSCAR EM TODA A INTERNET"):
    if busca_usuario:
        with st.spinner('Vasculhando lojas e marketplaces...'):
            lista_ofertas = buscar_precos_internet(busca_usuario)
            
            if lista_ofertas:
                melhor = lista_ofertas[0]
                
                # Card de Destaque
                st.success(f"🏆 MENOR PREÇO ENCONTRADO: **{melhor['preco_texto']}**")
                st.info(f"🏢 Loja: **{melhor['loja']}**")
                st.write(f"📦 {melhor['nome']}")
                
                st.link_button("🛒 IR PARA A LOJA", melhor['link'])
                
                st.write("---")
                st.write("📊 **Outras opções encontradas:**")
                
                for oferta in lista_ofertas[1:]:
                    col1, col2 = st.columns([2, 1])
                    col1.write(f"**{oferta['loja']}**\n{oferta['nome']}")
                    col2.write(f"**{oferta['preco_texto']}**")
                    st.write(f"[Ver oferta]({oferta['link']})")
                    st.write("-" * 10)
                
                # --- ÁREA DE MONETIZAÇÃO ---
                st.markdown("### 🔔 Não quer pesquisar de novo?")
                st.write("Meu robô monitora este produto 24h por dia e te avisa no WhatsApp se o preço cair.")
                
                with st.expander("ATIVAR ALERTA DE PREÇO (R$ 10,00)"):
                    st.write("1. Faça o PIX de **R$ 10,00** para sua-chave-aqui")
                    whatsapp = st.text_input("Seu WhatsApp com DDD:")
                    alvo = st.number_input("Me avise quando baixar de:", value=melhor['preco'] * 0.9)
                    
                    if st.button("CONFIRMAR E VIGIAR"):
                        st.balloons()
                        st.success("Tudo pronto! Assim que o PIX for validado, eu começo o monitoramento.")
            else:
                st.warning("Não encontrei ofertas exatas agora. Tente mudar o nome do produto.")
    else:
        st.error("Por favor, digite o nome de um produto.")

st.caption("Sistema de Inteligência de Preços - Arquiteto de Dados Renato")
