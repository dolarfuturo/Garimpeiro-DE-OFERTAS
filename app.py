import streamlit as st
import os
import requests
from gtts import gTTS
from moviepy.editor import AudioFileClip, ColorClip, CompositeVideoClip, TextClip

st.set_page_config(page_title="Gerador Rápido", layout="centered")
st.title("🎬 Gerador de Vídeo Lite")

api_key = st.secrets.get("GEMINI_API_KEY")

if st.button("🚀 GERAR VÍDEO"):
    status = st.empty()
    
    # 1. Roteiro (Simplificado)
    status.info("1/3 | Criando roteiro...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Escreva um roteiro de 30 segundos sobre tecnologia. Sem asteriscos."}]}]}
    res = requests.post(url, json=payload).json()
    texto = res['candidates'][0]['content']['parts'][0]['text']
    
    # 2. Áudio
    status.info("2/3 | Criando áudio...")
    tts = gTTS(text=texto, lang='pt')
    tts.save("audio.mp3")
    audio = AudioFileClip("audio.mp3")
    
    # 3. Vídeo (Fundo de cor sólida para garantir a renderização rápida)
    status.info("3/3 | Renderizando...")
    fundo = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=audio.duration)
    
    # Legenda simplificada sem usar PIL (evita erros de biblioteca)
    legenda = TextClip(texto, fontsize=50, color='white', size=(1000, None), method='caption').set_duration(audio.duration).set_position('center')
    
    video = CompositeVideoClip([fundo, legenda]).set_audio(audio)
    video.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    
    st.success("Vídeo pronto!")
    with open("final.mp4", "rb") as f:
        st.download_button("📥 BAIXAR", f, "video.mp4")
