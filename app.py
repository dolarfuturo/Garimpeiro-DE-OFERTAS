import streamlit as st
import os
import requests
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos (100% Gratuita)")
st.markdown("Configure o estilo do seu vídeo abaixo e deixe a IA trabalhar.")

# Puxando a chave automaticamente e de forma segura dos Secrets do Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se digitou GEMINI_API_KEY corretamente nas configurações.")
    st.stop()

with st.form(key="gerador_video"):
    # A CAIXA DA CHAVE API FOI REMOVIDA DA TELA!
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: Por que os grandes players usam paridade cambial")
    imagem_carregada = st.file_uploader("Suba sua imagem de fundo (.png ou .jpg)", type=["png", "jpg"])
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Áudio")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Apenas Música de Fundo", "Voz Narrada + Música de Fundo")
    )
    
    voz_escolhida = st.selectbox(
        "Escolha o Narrador (se houver voz):",
        ("pt-BR-FabioNeural (Masculino - Finanças)", "pt-BR-FranciscaNeural (Feminino - Dinâmico)")
    )
    cod_voz = voz_escolhida.split()[0]
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO GRATUITO")

if botao_gerar:
    if not tema or not imagem_carregada:
        st.error("❌ Por favor, preencha o Tema e envie a Imagem!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        with st.spinner("🤖 Google Gemini pensando no roteiro perfeito..."):
            try:
                # Requisição direta para o endpoint estável atual do Gemini 2.5 Flash
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "máximo 40 segundos de leitura" if "Voz" in tipo_audio else "máximo 140 caracteres"
                prompt = f"Escreva um texto curto e altamente focado em conversão/vendas para o TikTok sobre o tema: {tema}. Tamanho ideal: {tamanho_max}. Retorne APENAS o texto puro que vai na tela, sem indicações de cena, sem aspas e sem parênteses."
                
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                if response.status_code != 200:
                    st.error(f"Erro na API do Google: {response_json.get('error', {}).get('message', 'Erro desconhecido')}")
                    st.stop()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                st.info(f"📜 **Roteiro Gerado pelo Gemini:**\n\n_{texto_do_video}_")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []
                
                # ---- CRIAÇÃO DO ÁUDIO ----
                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner("🎙️ Gerando narração grátis..."):
                        async def gerar_voz():
                            communicate = edge_tts.Communicate(texto_do_video, cod_voz)
                            await communicate.save(audio_final_path)
                        asyncio.run(gerar_voz())
                        arquivos_para_limpar.append(audio_final_path)
                        duracao_video = AudioFileClip(audio_final_path).duration
                
                elif tipo_audio == "Apenas Música de Fundo":
                    with st.spinner("🎵 Processando música..."):
                        with open("musica_temp.mp3", "wb") as f:
                            f.write(musica_carregada.getbuffer())
                        arquivos_para_limpar.append("musica_temp.mp3")
                        audio_final_path = "musica_temp.mp3"
                        duracao_video = min(AudioFileClip(audio_final_path).duration, 15)
                
                elif tipo_audio == "Voz Narrada + Música de Fundo":
                    with st.spinner("🎛️ Combinando Voz + Música..."):
                        async def gerar_voz_dupla():
                            communicate = edge_tts.Communicate(texto_do_video, cod_voz)
                            await communicate.save("voz_temp.mp3")
                        asyncio.run(gerar_voz_dupla())
                        arquivos_para_limpar.append("voz_temp.mp3")
                        
                        with open("musica_temp.mp3", "wb") as f:
                            f.write(musica_carregada.getbuffer())
                        arquivos_para_limpar.append("musica_temp.mp3")
                        
                        v_clip = AudioFileClip("voz_temp.mp3")
                        m_clip = AudioFileClip("musica_temp.mp3").subclip(0, v_clip.duration).volumex(0.12)
                        
                        mixed_audio = CompositeAudioClip([v_clip, m_clip])
                        mixed_audio.write_audiofile("mix_final.mp3", logger=None)
                        arquivos_para_limpar.append("mix_final.mp3")
                        
                        audio_final_path = "mix_final.mp3"
                        duracao_video = v_clip.duration
                
                # ---- PROCESSANDO A IMAGEM ----
                with st.spinner("🎨 Aplicando design nas legendas..."):
                    imagem_fundo = Image.open(imagem_carregada)
                    imagem_fundo = imagem_fundo.resize((1080, 1920))
                    canvas = ImageDraw.Draw(imagem_fundo)
                    font = ImageFont.load_default()
                        
                    palavras = texto_do_video.split()
                    linhas = []
                    linha_atual = ""
                    for palavra in palavras:
                        if len(linha_atual + " " + palavra) < 25:
                            linha_atual = f"{linha_atual} {palavra}".strip()
                        else:
                            linhas.append(linha_atual)
                            linha_atual = palavra
                    if linha_atual: 
                        linhas.append(linha_atual)
                    
                    y_text = (1920 - (len(linhas) * 85)) // 2
                    for linha in list(dict.fromkeys(linhas)):
                        if linha:
                            canvas.text((100, y_text), linha, font=font, fill="white", stroke_width=2, stroke_fill="black")
                            y_text += 85
                        
                    imagem_fundo.save("fundo_final.png")
                    arquivos_para_limpar.append("fundo_final.png")
                
                # ---- RENDERIZANDO O VÍDEO FINAL ----
                with st.spinner("🎬 Criando MP4 final..."):
                    with AudioFileClip(audio_final_path) as audio_clip:
                        if tipo_audio == "Apenas Música de Fundo":
                            audio_clip = audio_clip.subclip(0, duracao_video)
                            
                        with ImageClip("fundo_final.png").set_duration(duracao_video) as video_img:
                            video_final = video_img.set_audio(audio_clip)
                            video_final.write_videofile(
                                "video_final_tiktok.mp4", fps=24, codec="libx264", 
                                audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                            )
                
                st.success("🎉 VÍDEO PRONTO E GERADO DE GRAÇA!")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR MEU VÍDEO",
                        data=file,
                        file_name="video_gratis.mp4",
                        mime="video/mp4"
                    )
                
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro no sistema: {e}")
