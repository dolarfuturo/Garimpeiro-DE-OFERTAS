import streamlit as st
import os
import requests
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, VideoFileClip, CompositeAudioClip

st.set_page_config(page_title="Super Gerador TikTok 2 em 1", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos Automatizada")
st.markdown("Escolha o modo de criação, configure os detalhes e deixe a IA trabalhar.")

# Garante que a API Key existe nos Secrets do Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

# 🎛️ SELETOR DE MODO
modo_criacao = st.radio(
    "💡 Escolha o Modo de Criação:",
    ("Foto Estática (Rápido)", "Vídeo de Fundo (Editor de Movimento)"),
    horizontal=True
)

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: Como limpar a casa em 20 minutos")
    
    if modo_criacao == "Foto Estática (Rápido)":
        imagem_carregada = st.file_uploader("Suba sua imagem de fundo (.png ou .jpg)", type=["png", "jpg"])
        video_carregado = None
    else:
        video_carregado = st.file_uploader("Suba seu vídeo de fundo em movimento (.mp4)", type=["mp4"])
        imagem_carregada = None
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Áudio")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Apenas Música de Fundo", "Voz Narrada + Música de Fundo")
    )
    
    voz_escolhida = st.selectbox(
        "Escolha o Idioma/Sotaque da Voz:",
        ("Português (Brasil)", "Português (Portugal)")
    )
    lang_code = "pt"
    tld_code = "com.br" if "Brasil" in voz_escolhida else "pt"
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO COMPLETO")

if botao_gerar:
    if not tema:
        st.error("❌ Por favor, preencha o Tema do vídeo!")
        st.stop()
        
    if modo_criacao == "Foto Estática (Rápido)" and not imagem_carregada:
        st.error("❌ No modo estático, você precisa enviar uma Imagem!")
        st.stop()
        
    if modo_criacao == "Vídeo de Fundo (Editor de Movimento)" and not video_carregado:
        st.error("❌ No modo editor, você precisa enviar um Vídeo .mp4 de fundo!")
        st.stop()
        
    if "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
        st.stop()

    with st.spinner("🤖 Google Gemini pensando no roteiro perfeito..."):
        try:
            # Chamada para o Gemini 2.5 Flash
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

            # ---- PROCESSAMENTO DO ÁUDIO ----
            if tipo_audio == "Apenas Voz Narrada":
                with st.spinner("🎙️ Gerando narração..."):
                    if criar_audio_gtts(texto_do_video, audio_final_path, lang_code, tld_code):
                        arquivos_para_limpar.append(audio_final_path)
                        duracao_video = AudioFileClip(audio_final_path).duration
                    else: st.stop()
            
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
                    else: st.stop()
            
            # ---- DESIGN DA IMAGEM TRANSPARENTE DA LEGENDA ----
            with st.spinner("🎨 Alinhando design e legendas..."):
                img_legenda = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
                canvas = ImageDraw.Draw(img_legenda)
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
                if linha_atual: linhas.append(linha_atual)
                
                y_text = (1920 - (len(linhas) * 85)) // 2
                for linha in list(dict.fromkeys(linhas)):
                    if linha:
                        canvas.text((100, y_text), linha, font=font, fill="white", stroke_width=2, stroke_fill="black")
                        y_text += 85
                    
                img_legenda.save("overlay_legenda.png")
                arquivos_para_limpar.append("overlay_legenda.png")

            # ---- RENDERIZADOR CORRIGIDO SEM ANTIALIAS ----
            with st.spinner("🎬 Renderizando arquivo MP4 final..."):
                with AudioFileClip(audio_final_path) as audio_clip:
                    if tipo_audio == "Apenas Música de Fundo":
                        audio_clip = audio_clip.subclip(0, duracao_video)
                    
                    # MODO 1: Foto Estática
                    if modo_criacao == "Foto Estática (Rápido)":
                        # Correção aqui: removido qualquer menção interna ao método antigo de resize
                        imagem_fundo = Image.open(imagem_carregada).resize((1080, 1920))
                        legenda_overlay = Image.open("overlay_legenda.png")
                        imagem_fundo.paste(legenda_overlay, (0,0), legenda_overlay)
                        imagem_fundo.save("fundo_com_legenda.png")
                        arquivos_para_limpar.append("fundo_com_legenda.png")
                        
                        video_base = ImageClip("fundo_com_legenda.png").set_duration(duracao_video)
                        video_final = video_base.set_audio(audio_clip)
                    
                    # MODO 2: Vídeo com Movimento (Editor)
                    else:
                        with open("video_fundo_temp.mp4", "wb") as f:
                            f.write(video_carregado.getbuffer())
                        arquivos_para_limpar.append("video_fundo_temp.mp4")
                        
                        # Carrega e ajusta o vídeo .mp4 sem usar filtros obsoletos de redimensionamento
                        video_base = VideoFileClip("video_fundo_temp.mp4")
                        video_base = video_base.resize(newsize=(1080, 1920))
                        
                        if video_base.duration < duracao_video:
                            video_base = video_base.loop(duration=duracao_video)
                        else:
                            video_base = video_base.subclip(0, duracao_video)
                            
                        legenda_clip = ImageClip("overlay_legenda.png").set_duration(duracao_video)
                        from moviepy.video.VideoClip import CompositeVideoClip
                        video_final = CompositeVideoClip([video_base, legenda_clip]).set_audio(audio_clip)
                    
                    # Exportação definitiva
                    video_final.write_videofile(
                        "video_final_tiktok.mp4", fps=24, codec="libx264", 
                        audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                    )
            
            st.success("🎉 VÍDEO COMPLETADO COM SUCESSO!")
            
            with open("video_final_tiktok.mp4", "rb") as file:
                st.download_button(
                    label="📥 BAIXAR MEU VÍDEO FINAL",
                    data=file,
                    file_name="video_tiktok_ia.mp4",
                    mime="video/mp4"
                )
            
            arquivos_para_limpar.append("video_final_tiktok.mp4")
            for arquivo in arquivos_para_limpar:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    
        except Exception as e:
            st.error(f"Erro inesperado no sistema: {e}")
