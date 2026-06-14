import streamlit as st
import os
import requests
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos Rápida (Imagem + Tema)")
st.markdown("Insira o tema, suba sua foto de fundo e crie um vídeo narrado pela IA em segundos.")

# Garante que a API Key existe nos Secrets do Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: Por que os grandes players usam paridade cambial")
    imagem_carregada = st.file_uploader("Suba sua imagem de fundo (.png ou .jpg)", type=["png", "jpg"])
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Áudio")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Apenas Música de Fundo", "Voz Narrada + Música de Fundo")
    )
    
    voz_escolhida = st.selectbox(
        "Escolha o Sotaque da Voz:",
        ("Português (Brasil)", "Português (Portugal)")
    )
    lang_code = "pt"
    tld_code = "com.br" if "Brasil" in voz_escolhida else "pt"
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO RÁPIDO")

if botao_gerar:
    if not tema or not imagem_carregada:
        st.error("❌ Por favor, preencha o Tema e envie a Imagem!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        with st.spinner("🤖 Google Gemini pensando no roteiro perfeito..."):
            try:
                # Chamada direta para o Gemini 2.5 Flash via API estável
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "máximo 35 segundos de leitura" if "Voz" in tipo_audio else "máximo 140 caracteres"
                prompt = f"Escreva um texto curto e focado em conversão/vendas para o TikTok sobre o tema: {tema}. Tamanho: {tamanho_max}. Retorne APENAS o texto puro, sem indicações de cena, sem aspas, sem asteriscos e sem parênteses."
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                if response.status_code != 200:
                    st.error(f"Erro na API do Google: {response_json.get('error', {}).get('message', 'Erro desconhecido')}")
                    st.stop()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '')
                st.info(f"📜 **Roteiro Gerado pelo Gemini:**\n\n_{texto_do_video}_")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []

                # ---- MOTOR DE ÁUDIO ESTÁVEL (gTTS) ----
                def criar_audio_gtts(texto, caminho_saida, lang, tld):
                    try:
                        tts = gTTS(text=texto, lang=lang, tld=tld, slow=False)
                        tts.save(caminho_saida)
                        return True
                    except Exception as e:
                        st.error(f"Erro ao gerar áudio: {e}")
                        return False

                # ---- CRIAÇÃO DO ÁUDIO ----
                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner("🎙️ Gerando narração..."):
                        if criar_audio_gtts(texto_do_video, audio_final_path, lang_code, tld_code):
                            arquivos_para_limpar.append(audio_final_path)
                            duracao_video = AudioFileClip(audio_final_path).duration
                        else:
                            st.stop()
                
                elif tipo_audio == "Apenas Música de Fundo":
                    with st.spinner("🎵 Processando música..."):
                        with open("musica_temp.mp3", "wb") as f:
                            f.write(musica_carregada.getbuffer())
                        arquivos_para_limpar.append("musica_temp.mp3")
                        audio_final_path = "musica_temp.mp3"
                        duracao_video = min(AudioFileClip(audio_final_path).duration, 15)
                
                elif tipo_audio == "Voz Narrada + Música de Fundo":
                    with st.spinner("🎛️ Combinando Voz + Música..."):
                        if criar_audio_gtts(texto_do_video, "voz_temp.mp3", lang_code, tld_code):
                            arquivos_para_limpar.append("voz_temp.mp3")
                            
                            with open("musica_temp.mp3", "wb") as f:
                                f.write(musica_carregada.getbuffer())
                            arquivos_para_limpar.append("musica_temp.mp3")
                            
                            v_clip = AudioFileClip("voz_temp.mp3")
                            m_clip = AudioFileClip("musica_temp.mp3").subclip(0, v_clip.duration).volumex(0.15)
                            
                            mixed_audio = CompositeAudioClip([v_clip, m_clip])
                            mixed_audio.write_audiofile("mix_final.mp3", logger=None)
                            arquivos_para_limpar.append("mix_final.mp3")
                            
                            audio_final_path = "mix_final.mp3"
                            duracao_video = v_clip.duration
                        else:
                            st.stop()
                
                # ---- PROCESSANDO A IMAGEM E LEGENDA (Sem métodos antigos/obsoletos) ----
                with st.spinner("🎨 Alinhando design e legendas..."):
                    imagem_fundo = Image.open(imagem_carregada)
                    imagem_fundo = imagem_fundo.resize((1080, 1920))
                    canvas = ImageDraw.Draw(imagem_fundo)
                    font = ImageFont.load_default()
                        
                    palavras = texto_do_video.split()
                    linhas = []
                    linha_atual = ""
                    for palavra in palavras:
                        if len(linha_atual + " " + palavra) < 28:
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
                with st.spinner("🎬 Juntando tudo no MP4 final..."):
                    with AudioFileClip(audio_final_path) as audio_clip:
                        if tipo_audio == "Apenas Música de Fundo":
                            audio_clip = audio_clip.subclip(0, duracao_video)
                            
                        with ImageClip("fundo_final.png").set_duration(duracao_video) as video_img:
                            video_final = video_img.set_audio(audio_clip)
                            video_final.write_videofile(
                                "video_final_tiktok.mp4", fps=24, codec="libx264", 
                                audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                            )
                
                st.success("🎉 VÍDEO COMPLETADO COM SUCESSO!")
                
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
                st.error(f"Erro inesperado no sistema: {e}")
