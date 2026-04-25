import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuração da Página para Mobile
st.set_page_config(page_title="Garimpeiro K97", page_icon="💰", layout="centered")

# Estilo para botões grandes e interface limpa
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        width: 100%;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Garimpeiro K97")
st.subheader("Encontre o menor preço e economize real.")

# --- SEÇÃO DE BUSCA ---
produto = st.text_input("O que você quer comprar?", placeholder="Ex: iPhone 15 128gb")

if st.button("🔍 BUSCAR MENOR PREÇO"):
    if produto:
        with st.spinner('Garimpando as melhores ofertas...'):
            # Simulação de Web Scraping (Aqui entra a lógica de busca real)
            # Para o exemplo, vamos simular resultados:
            ofertas = [
                {"loja": "Mercado Livre", "preco": 4750.00, "link": "https://www.mercadolivre.com.br"},
                {"loja": "Amazon", "preco": 4899.00, "link": "https://www.amazon.com.br"},
                {"loja": "Magalu", "preco": 4950.00, "link": "https://www.magalu.com.br"}
            ]
            
            df = pd.DataFrame(ofertas)
            menor_preco = df.loc[df['preco'].idxmin()]

            # Exibição do Resultado Principal
            st.success(f"✅ MELHOR OFERTA: R$ {menor_preco['preco']:.2f}")
            st.info(f"📍 Disponível em: **{menor_preco['loja']}**")
            
            st.link_button(f"🛒 IR PARA A LOJA", menor_preco['link'])
            
            st.write("---")
            
            # --- SEÇÃO DE MONETIZAÇÃO (O SEU LUCRO) ---
            st.warning("⚠️ **AINDA ESTÁ CARO?**")
            st.write("Não perca tempo pesquisando todo dia. Meu robô vigia o preço para você 24h por dia!")
            
            with st.expander("🔔 ATIVAR MONITORAMENTO (R$ 10,00)"):
                st.write("Para ativar o monitoramento automático via WhatsApp:")
                st.write("1️⃣ Faça um PIX de **R$ 10,00** (Taxa Única).")
                st.code("SUA-CHAVE-PIX-AQUI", language="text") # Coloque sua chave aqui
                
                whatsapp = st.text_input("Seu WhatsApp (com DDD):")
                preco_alvo = st.number_input("Me avise quando baixar de (R$):", value=float(menor_preco['preco']-100))
                
                if st.button("CONFIRMAR PAGAMENTO E ATIVAR"):
                    if whatsapp:
                        # Aqui o código enviará para sua Planilha Google futuramente
                        st.balloons()
                        st.success("SOLICITAÇÃO ENVIADA! Assim que o PIX cair, o robô assume a vigília. 🤖")
                        # Log para você ver no terminal/planilha:
                        print(f"Novo monitoramento: {whatsapp} | {produto} | Alvo: {preco_alvo}")
                    else:
                        st.error("Por favor, insira seu WhatsApp.")
    else:
        st.error("Digite o nome de um produto para buscar.")

# Rodapé
st.caption("Desenvolvido por Arquiteto de Dados K97 - 2026")
