import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

# Configuração Mobile
st.set_page_config(page_title="Garimpeiro de Ofertas", page_icon="💰")

# Estilo visual para celular
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div.stButton > button:first-child {
        height: 3.5em; width: 100%; border-radius: 10px;
        font-size: 20px; font-weight: bold; background-color: #007bff; color: white;
    }
    .preco-card {
        background-color: white; padding: 20px; border-radius: 15px;
        border-left: 5px solid #28a745; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Garimpeiro de Ofertas")
st.write("Busca em tempo real: Farmácias, Marketplaces e Lojas.")

# --- FUNÇÃO DE BUSCA (VÁRIAS FONTES) ---
def garimpar(produto):
    resultados = []
    termo = urllib.parse.quote(produto)
    
    # Tentativa 1: Google Shopping (Agregador de Farmácias/Lojas)
    url_google = f"https://www.google.com/search?q={termo}&tbm=shop&hl=pt-BR&gl=br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url_google, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Seletores para pegar os cards de produtos
        for item in soup.select('.sh-dgr__content')[:5]:
            try:
                nome = item.select_one('h3').text
                loja = item.select_one('.aULzUe').text if item.select_one('.aULzUe') else "Lo_ja Online"
                preco_txt = item.select_one('.a88X0c').text
                link = item.select_one('a')['href']
                if link.startswith('/'): link = "https://www.google.com" + link
                
                # Limpeza numérica do preço
                valor = float(preco_txt.replace('R$', '').replace('.','').replace(',','.').strip())
                
                resultados.append({"loja": loja, "nome": nome, "preco": valor, "preco_txt": preco_txt, "link": link})
            except: continue
    except: pass
    
    return sorted(resultados, key=lambda x: x['preco'])

# --- INTERFACE DO USUÁRIO ---
query = st.text_input("O que você quer comprar hoje?", placeholder="Ex: Fralda Pampers G")

if st.button("🔍 GARIMPAR INTERNET"):
    if query:
        with st.spinner('O robô está entrando nos sites...'):
            dados = garimpar(query)
            
            if dados:
                melhor = dados[0]
                
                # Exibição do Melhor Preço
                st.markdown(f"""
                <div class="preco-card">
                    <h3 style='margin:0; color:#28a745;'>🏆 MELHOR PREÇO</h3>
                    <p style='font-size:24px; font-weight:bold; margin:5px 0;'>{melhor['preco_txt']}</p>
                    <p style='margin:0; color:#555;'>Loja: <b>{melhor['loja']}</b></p>
                    <p style='font-size:12px; color:#888;'>{melhor['nome']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.link_button("➡️ IR PARA A LOJA", melhor['link'])
                
                # Outras Opções
                with st.expander("Ver outras lojas encontradas"):
                    for d in dados[1:]:
                        st.write(f"**{d['preco_txt']}** na {d['loja']}")
                        st.caption(d['nome'])
                        st.write(f"[Acesse aqui]({d['link']})")
                        st.divider()

                # --- MÓDULO DE MONETIZAÇÃO (PIX) ---
                st.write("---")
                st.subheader("🔔 Monitoramento 24h")
                st.write("Quer que eu te avise se esse preço cair mais?")
                
                with st.expander("ATIVAR ALERTA NO WHATSAPP (R$ 10,00)"):
                    st.write("1. Faça o PIX para: **SUA-CHAVE-AQUI**")
                    zap = st.text_input("Seu WhatsApp:")
                    if st.button("ATIVAR MEU ROBÔ"):
                        st.success("Pedido enviado! Assim que o PIX cair, o monitoramento começa.")
                        st.balloons()
            else:
                st.error("O Google bloqueou a busca automatica. Tente novamente em instantes ou simplifique o nome.")
    else:
        st.warning("Digite um produto.")

st.divider()
st.caption("Arquiteto de Dados Renato - 2026")
