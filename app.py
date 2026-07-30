import streamlit as st
import os
import requests
import asyncio
import edge_tts # NOVO MOTOR DE VOZ NEURAL (Humana)
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos (Voz Humana + Legenda Dinâmica)")
st.markdown("Configure o estilo do seu vídeo abaixo e deixe a IA trabalhar.")

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
    st.subheader("🎵 Configurações de Áudio e Voz")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Voz Narrada + Música de Fundo", "Apenas Música de Fundo")
    )
    
    # NOVAS VOZES HUMANIZADAS (Microsoft Azure Neurais)
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
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO GRATUITO")

# --- FUNÇÃO ASSÍNCRONA PARA GERAR VOZ COM EDGE-TTS ---
async def gerar_audio_neural(texto, caminho_saida, voz):
    try:
        communicate = edge_tts.Communicate(texto, voz)
        await communicate.save(caminho_saida)
        return True
    except Exception as e:
        return False

if botao_gerar:
    if not tema or not imagem_carregada:
        st.error("❌ Por favor, preencha o Tema e envie a Imagem!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        with st.spinner("🤖 Google Gemini pensando no roteiro perfeito..."):
            try:
                # API Gemini
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "máximo 35 segundos de leitura" if "Voz" in tipo_audio else "máximo 140 caracteres"
                prompt = f"Escreva um texto curto e focado em conversão/vendas para o TikTok sobre o tema: {tema}. Tamanho: {tamanho_max}. Retorne APENAS o texto puro, sem indicações de cena, sem aspas, sem asteriscos e sem parênteses."
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '')
                st.info(f"📜 **Roteiro Gerado:**\n\n_{texto_do_video}_")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []

                # ---- CRIAÇÃO DO ÁUDIO NEURAL ----
                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner("🎙️ Gerando narração com voz humana..."):
                        sucesso = asyncio.run(gerar_audio_neural(texto_do_video, audio_final_path, voice_id))
                        if sucesso:
                            arquivos_para_limpar.append(audio_final_path)
                            duracao_audio = AudioFileClip(audio_final_path).duration
                        else:
                            st.error("Erro ao gerar áudio.")
                            st.stop()
                
                elif tipo_audio == "Voz Narrada + Música de Fundo":
                    with st.spinner("🎛️ Combinando Voz Humana + Música..."):
                        sucesso = asyncio.run(gerar_audio_neural(texto_do_video, "voz_temp.mp3", voice_id))
                        if sucesso:
                            arquivos_para_limpar.append("voz_temp.mp3")
                            
                            with open("musica_temp.mp3", "wb") as f:
                                f.write(musica_carregada.getbuffer())
                            arquivos_para_limpar.append("musica_temp.mp3")
                            
                            v_clip = AudioFileClip("voz_temp.mp3")
                            m_clip = AudioFileClip("musica_temp.mp3").subclip(0, v_clip.duration).volumex(0.10) # Música baixinha
                            
                            mixed_audio = CompositeAudioClip([v_clip, m_clip])
                            mixed_audio.write_audiofile("mix_final.mp3", logger=None)
                            arquivos_para_limpar.append("mix_final.mp3")
                            
                            audio_final_path = "mix_final.mp3"
                            duracao_audio = v_clip.duration
                        else:
                            st.stop()
                
                elif tipo_audio == "Apenas Música de Fundo":
                    # Lógica original para apenas música
                    with open("musica_temp.mp3", "wb") as f:
                        f.write(musica_carregada.getbuffer())
                    arquivos_para_limpar.append("musica_temp.mp3")
                    audio_final_path = "musica_temp.mp3"
                    duracao_audio = min(AudioFileClip(audio_final_path).duration, 15)

                # ---- PROCESSANDO IMAGEM COM LEGENDAS DINÂMICAS NA PARTE DE BAIXO ----
                with st.spinner("🎨 Criando legendas sincronizadas..."):
                    imagem_fundo_base = Image.open(imagem_carregada).resize((1080, 1920))
                    
                    try:
                        # Tenta carregar uma fonte maior e mais bonita (se houver no sistema)
                        font = ImageFont.truetype("arial.ttf", 60)
                    except:
                        # Fallback se não achar fonte (fica pequeno, o ideal é colocar um arquivo .ttf na pasta do projeto)
                        font = ImageFont.load_default()

                    clips_de_video = []
                    
                    if "Voz" in tipo_audio:
                        # Dividir o texto em "pedaços" de 4 palavras (Legenda dinâmica)
                        palavras = texto_do_video.split()
                        tamanho_grupo = 4 
                        
                        grupos_de_palavras = [" ".join(palavras[i:i + tamanho_grupo]) for i in range(0, len(palavras), tamanho_grupo)]
                        
                        total_caracteres = len(texto_do_video)
                        
                        # Criar um trecho de vídeo para cada frase
                        for i, frase in enumerate(grupos_de_palavras):
                            # Calcula quanto tempo essa frase vai ficar na tela baseado no tamanho dela
                            peso_da_frase = len(frase) / total_caracteres
                            duracao_frase = duracao_audio * peso_da_frase
                            
                            # Cria a imagem dessa frase específica
                            img_frame = imagem_fundo_base.copy()
                            canvas = ImageDraw.Draw(img_frame)
                            
                            # Calcular posição para centralizar no eixo X, e colocar em baixo no Y (ex: 1500)
                            # Se der erro no textbbox, usamos um fallback simples
                            try:
                                bbox = canvas.textbbox((0, 0), frase, font=font)
                                largura_texto = bbox[2] - bbox[0]
                            except:
                                largura_texto = len(frase) * 15 # estimativa se o bbox falhar
                                
                            pos_x = (1080 - largura_texto) // 2
                            pos_y = 1450 # Fica na parte inferior do vídeo
                            
                            # Fundo preto para a legenda dar leitura (efeito de sombra grossa)
                            canvas.text((pos_x+3, pos_y+3), frase, font=font, fill="black")
                            canvas.text((pos_x, pos_y), frase, font=font, fill="white")
                            
                            nome_frame = f"frame_temp_{i}.png"
                            img_frame.save(nome_frame)
                            arquivos_para_limpar.append(nome_frame)
                            
                            # Transforma a imagem em um clipe com o tempo exato da fala
                            clip_img = ImageClip(nome_frame).set_duration(duracao_frase)
                            clips_de_video.append(clip_img)
                            
                        # Junta todas as imagens dinâmicas num vídeo só (sem áudio ainda)
                        video_final_sem_audio = concatenate_videoclips(clips_de_video, method="compose")
                    
                    else:
                        # Se for só música, gera apenas 1 imagem parada com o texto no meio
                        video_final_sem_audio = ImageClip("fundo_final.png").set_duration(duracao_audio)

                # ---- RENDERIZANDO O VÍDEO FINAL COM AUDIO E LEGENDA ----
                with st.spinner("🎬 Juntando tudo no MP4 final (isso pode levar uns segundos)..."):
                    audio_clip = AudioFileClip(audio_final_path)
                    
                    # Junta o video das legendas pulando com o áudio final
                    video_final = video_final_sem_audio.set_audio(audio_clip)
                    
                    video_final.write_videofile(
                        "video_final_tiktok.mp4", fps=24, codec="libx264", 
                        audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                    )
                
                st.success("🎉 VÍDEO COMPLETADO COM SUCESSO!")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR MEU VÍDEO",
                        data=file,
                        file_name="video_viral.mp4",
                        mime="video/mp4"
                    )
                
                # Limpeza de memória
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
