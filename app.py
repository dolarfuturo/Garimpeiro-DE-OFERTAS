import streamlit as st
import os
import requests
import asyncio
import edge_tts 
import re
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeAudioClip
import textwrap

st.set_page_config(page_title="Super Gerador TikTok LIVE", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos (Fundo em Vídeo + Foco em LIVE)")
st.markdown("Configure o tema do seu vídeo voltado para incentivar transmissões ao vivo e deixe a IA trabalhar.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo (ex: dicas de transmissão, rotina de viagens em live)?", placeholder="Ex: Como transmitir sua viagem de carro ao vivo no TikTok")
    video_carregado = st.file_uploader("Suba seu vídeo de fundo (.mp4)", type=["mp4", "mov"])
    
    st.markdown("---")
    st.subheader("🎨 Configurações de Estilo da Legenda")
    
    cor_legenda = st.selectbox(
        "Cor da Legenda:",
        ["Branco", "Amarelo", "Verde Neon", "Ciano"]
    )
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Áudio e Voz")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Voz Narrada + Música de Fundo", "Apenas Música de Fundo")
    )
    
    vozes_disponiveis = {
        "Antonio (Masculino - BR)": "pt-BR-AntonioNeural",
        "Francisca (Feminino - BR)": "pt-BR-FranciscaNeural",
        "Duarte (Masculino - PT)": "pt-PT-DuarteNeural",
        "Raquel (Feminino - PT)": "pt-PT-RaquelNeural"
    }
    
    voz_escolhida = st.selectbox("Escolha a Voz Neural (Ultra Realista):", list(vozes_disponiveis.keys()))
    voice_id = vozes_disponiveis[voz_escolhida]
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO PARA TIKTOK LIVE")

async def gerar_audio_neural(texto, caminho_saida, voz):
    try:
        communicate = edge_tts.Communicate(texto, voz, rate="-10%")
        await communicate.save(caminho_saida)
        return True
    except Exception as e:
        return False

if botao_gerar:
    if not tema or not video_carregado:
        st.error("❌ Por favor, preencha o Tema e envie o Vídeo de fundo (.mp4)!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        with st.spinner("🤖 Google Gemini criando o roteiro focado em LIVE..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "cerca de 135 a 145 palavras" if "Voz" in tipo_audio else "máximo 140 caracteres"
                
                prompt = f"""Escreva um roteiro dinâmico e envolvente para TikTok/Shorts sobre o tema: '{tema}'.
                O tom deve ser natural, amigável e instigante, focado em incentivar criadores ou espectadores a abrirem transmissões ao vivo ou acompanharem lives.
                REGRA OBRIGATÓRIA 1: O roteiro DEVE induzir o espectador a ficar no vídeo até o final, criando curiosidade contínua e terminando com um gancho forte que o faça interagir ou pensar em fazer uma live.
                REGRA OBRIGATÓRIA 2: O texto total deve ter {tamanho_max}.
                REGRA OBRIGATÓRIA 3: NUNCA repita palavras, sílabas ou crie gaguejos no final das frases. Escreva de forma limpa e natural.
                Retorne APENAS o texto puro, sem indicações de cena, sem aspas, sem asteriscos, sem hashtags e sem parênteses."""
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '')
                
                texto_do_video = texto_do_video.strip()
                if not texto_do_video.endswith(('.', '!', '?')):
                    texto_do_video += '.'
                
                palavras = texto_do_video.split()
                if len(palavras) > 1:
                    ultima_limpa = re.sub(r'[^\w]', '', palavras[-1]).lower()
                    penultima_limpa = re.sub(r'[^\w]', '', palavras[-2]).lower()
                    if ultima_limpa == penultima_limpa or (ultima_limpa.startswith(penultima_limpa) and len(ultima_limpa) > len(penultima_limpa)):
                        palavras.pop()
                        texto_do_video = " ".join(palavras)
                        if not texto_do_video.endswith('.'):
                            texto_do_video += '.'
                
                st.info(f"📜 **Roteiro Gerado (Total: {len(texto_do_video.split())} palavras):**\n\n_{texto_do_video}_")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []

                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner("🎙️ Gerando narração limpa e sem falhas..."):
                        sucesso = asyncio.run(gerar_audio_neural(texto_do_video, audio_final_path, voice_id))
                        if sucesso:
                            arquivos_para_limpar.append(audio_final_path)
                            duracao_audio = AudioFileClip(audio_final_path).duration
                        else:
                            st.error("Erro ao gerar áudio.")
                            st.stop()
                
                elif tipo_audio == "Voz Narrada + Música de Fundo":
                    with st.spinner("🎛️ Combinando Voz + Música..."):
                        sucesso = asyncio.run(gerar_audio_neural(texto_do_video, "voz_temp.mp3", voice_id))
                        if sucesso:
                            arquivos_para_limpar.append("voz_temp.mp3")
                            
                            with open("musica_temp.mp3", "wb") as f:
                                f.write(musica_carregada.getbuffer())
                            arquivos_para_limpar.append("musica_temp.mp3")
                            
                            v_clip = AudioFileClip("voz_temp.mp3")
                            m_clip = AudioFileClip("musica_temp.mp3").subclip(0, v_clip.duration).volumex(0.10)
                            
                            mixed_audio = CompositeAudioClip([v_clip, m_clip])
                            mixed_audio.write_audiofile("mix_final.mp3", logger=None)
                            arquivos_para_limpar.append("mix_final.mp3")
                            
                            audio_final_path = "mix_final.mp3"
                            duracao_audio = v_clip.duration
                        else:
                            st.stop()
                
                elif tipo_audio == "Apenas Música de Fundo":
                    with open("musica_temp.mp3", "wb") as f:
                        f.write(musica_carregada.getbuffer())
                    arquivos_para_limpar.append("musica_temp.mp3")
                    audio_final_path = "musica_temp.mp3"
                    duracao_audio = min(AudioFileClip(audio_final_path).duration, 65)

                with st.spinner("🎨 Processando o vídeo de fundo e legendas..."):
                    caminho_video_temp = "video_upload_temp.mp4"
                    with open(caminho_video_temp, "wb") as f:
                        f.write(video_carregado.getbuffer())
                    arquivos_para_limpar.append(caminho_video_temp)
                    
                    video_base = VideoFileClip(caminho_video_temp)
                    
                    if video_base.duration < duracao_audio:
                        video_base = video_base.loop(duration=duracao_audio)
                    else:
                        video_base = video_base.subclip(0, duracao_audio)
                    
                    w, h = video_base.size
                    tamanho_alvo_w, tamanho_alvo_h = 1080, 1920
                    
                    escala = max(tamanho_alvo_w / w, tamanho_alvo_h / h)
                    video_redimensionado = video_base.resize(escala)
                    video_cortado = video_redimensionado.crop(
                        x_center=video_redimensionado.w / 2,
                        y_center=video_redimensionado.h / 2,
                        width=tamanho_alvo_w,
                        height=tamanho_alvo_h
                    )
                    
                    mapa_cores = {
                        "Branco": "white",
                        "Amarelo": "#FFD700",
                        "Verde Neon": "#00FF66",
                        "Ciano": "#00FFFF"
                    }
                    cor_texto = mapa_cores[cor_legenda]

                    try:
                        font = ImageFont.truetype("fonte.ttf", 32)
                    except:
                        try:
                            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
                        except:
                            font = ImageFont.load_default()

                    linhas_roteiro = textwrap.wrap(texto_do_video, width=42)
                    
                    def add_text_to_frame(get_frame, t):
                        frame = get_frame(t)
                        img_frame = Image.fromarray(frame)
                        canvas = ImageDraw.Draw(img_frame)
                        
                        y_inicial = 820 
                        for linha in linhas_roteiro:
                            try:
                                bbox = canvas.textbbox((0, 0), linha, font=font)
                                largura_linha = bbox[2] - bbox[0]
                            except:
                                largura_linha = len(linha) * 17
                                
                            pos_x = (1080 - largura_linha) // 2
                            
                            canvas.text((pos_x+3, y_inicial+3), linha, font=font, fill="black")
                            canvas.text((pos_x+3, y_inicial-3), linha, font=font, fill="black")
                            canvas.text((pos_x-3, y_inicial+3), linha, font=font, fill="black")
                            canvas.text((pos_x-3, y_inicial-3), linha, font=font, fill="black")
                            
                            canvas.text((pos_x, y_inicial), linha, font=font, fill=cor_texto)
                            y_inicial += 40
                            
                        import numpy as np
                        return np.array(img_frame)

                    video_com_legenda = video_cortado.fl(add_text_to_frame)

                with st.spinner("🎬 Renderizando vídeo final com movimento..."):
                    audio_clip = AudioFileClip(audio_final_path)
                    video_final = video_com_legenda.set_audio(audio_clip)
                    
                    video_final.write_videofile(
                        "video_final_tiktok.mp4", fps=24, codec="libx264", 
                        audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                    )
                
                minutos = int(duracao_audio // 60)
                segundos = int(duracao_audio % 60)
                
                st.success(f"🎉 VÍDEO PRONTO! Duração: {minutos}m {segundos}s.")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR MEU VÍDEO PARA LIVE",
                        data=file,
                        file_name="video_para_live.mp4",
                        mime="video/mp4"
                    )
                
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
