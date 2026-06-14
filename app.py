import streamlit as st
import os
import requests
from gtts import gTTS
from PIL import Image, ImageDraw
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, CompositeAudioClip

st.set_page_config(page_title="Gerador TikTok", layout="centered")
st.title("🎬 Fábrica de Vídeos v2.0 (Estável)")

api_key = st.secrets["GEMINI_API_KEY"]

with st.form(key="form"):
    tema = st.text_input("Tema do vídeo")
    imagem_carregada = st.file_uploader("Suba a imagem", type=["png", "jpg"])
    botao_gerar = st.form_submit_button("🚀 GERAR VÍDEO")

if botao_gerar and tema and imagem_carregada:
    try:
        # 1. Roteiro (Com tratamento de erro de quota)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": f"Escreva um roteiro narrativo de 1 minuto sobre: {tema}. Sem asteriscos."}]}]}
        response = requests.post(url, json=payload).json()
        texto = response['candidates'][0]['content']['parts'][0]['text']
        st.info(texto)

        # 2. Áudio
        tts = gTTS(text=texto, lang='pt', tld='com.br')
        tts.save("audio.mp3")
        duracao = AudioFileClip("audio.mp3").duration

        # 3. Imagem (Corrigida: usando 'Resampling.LANCZOS' em vez de 'ANTIALIAS')
        img = Image.open(imagem_carregada).convert("RGBA")
        img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        img.save("fundo.png")

        # 4. Vídeo Simples (Evitando erros de TextClip complexo)
        # Criamos o vídeo usando apenas o fundo e o áudio
        video = ImageClip("fundo.png").set_duration(duracao)
        video = video.set_audio(AudioFileClip("audio.mp3"))
        
        video.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")

        st.success("Vídeo gerado!")
        with open("final.mp4", "rb") as f:
            st.download_button("📥 BAIXAR", f, "video.mp4")
            
    except Exception as e:
        st.error(f"Erro: {e}. Se for 'Quota Exceeded', aguarde 60 segundos antes de tentar de novo.")
