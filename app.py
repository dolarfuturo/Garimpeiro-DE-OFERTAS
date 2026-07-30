import streamlit as st
import os
import requests
import asyncio
import edge_tts 
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos (Voz Humana + Legenda Dinâmica)")
st.markdown("Configure o estilo do seu vídeo abaixo e deixe a IA trabalhar.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: Por que os grandes players usam paridade cambial")
    imagem_carregada = st.file_uploader("Suba sua imagem de fundo (.png ou .jpg)", type=["png", "jpg"])
    
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
    botao_gerar = st.form_submit_button(label="🚀 GERAR MEU VÍDEO GRATUITO")

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
        with st.spinner("🤖 Google Gemini criando um roteiro polêmico e garantindo mais de 1 minuto..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "EXATAMENTE entre 170 e 190 palavras" if "Voz" in tipo_audio else "máximo 140 caracteres"
                
                prompt = f"""Escreva um roteiro para TikTok/Shorts sobre o tema: '{tema}'.
                O tom deve ser EXALTADO, PROVOCATIVO e um pouco POLÊMICO para prender a atenção e gerar debate na audiência.
                REGRA OBRIGATÓRIA 1: O roteiro DEVE terminar com uma afirmação forte, absoluta e controversa (uma "verdade nua e crua") que deixe a audiência revoltada ou com muita vontade de debater. NÃO peça para curtir, compartilhar ou comentar. Apenas jogue a bomba e termine o vídeo abruptamente.
                REGRA OBRIGATÓRIA 2: O texto total deve ter {tamanho_max}. Isso garante obrigatoriamente que o vídeo ultrapasse 1 minuto para fins de monetização.
                Retorne APENAS o texto puro, sem indicações de cena, sem aspas, sem asteriscos, sem hashtags e sem parênteses."""
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '')
                
                st.info(f"📜 **Roteiro Gerado (Total: {len(texto_do_video.split())} palavras):**\n\n_{texto_do_video}_")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []

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
                    duracao_audio = min(AudioFileClip(audio_final_path).duration, 15)

                with st.spinner("🎨 Criando legendas sincronizadas sem atraso..."):
                    imagem_fundo_base = Image.open(imagem_carregada).resize((1080, 1920))
                    
                    mapa_cores = {
                        "Branco": "white",
                        "Amarelo": "#FFD700",
                        "Verde Neon": "#00FF66",
                        "Ciano": "#00FFFF"
                    }
                    cor_texto = mapa_cores[cor_legenda]

                    try:
                        font = ImageFont.truetype("fonte.ttf", 60)
                    except:
                        try:
                            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
                        except:
                            font = ImageFont.load_default()

                    clips_de_video = []
                    
                    if "Voz" in tipo_audio:
                        palavras = texto_do_video.split()
                        tamanho_grupo = 4 
                        
                        grupos_de_palavras = [" ".join(palavras[i:i + tamanho_grupo]) for i in range(0, len(palavras), tamanho_grupo)]
                        total_palavras_roteiro = len(palavras)
                        
                        for i, frase in enumerate(grupos_de_palavras):
                            # Sincronização exata por proporção de palavras (sem acumular atraso no final)
                            palavras_na_frase = len(frase.split())
                            peso_da_frase = palavras_na_frase / total_palavras_roteiro
                            duracao_frase = duracao_audio * peso_da_frase
                            
                            img_frame = imagem_fundo_base.copy()
                            canvas = ImageDraw.Draw(img_frame)
                            
                            try:
                                bbox = canvas.textbbox((0, 0), frase, font=font)
                                largura_texto = bbox[2] - bbox[0]
                            except:
                                largura_texto = len(frase) * 35 
                                
                            pos_x = (1080 - largura_texto) // 2
                            pos_y = 1550 
                            
                            canvas.text((pos_x+5, pos_y+5), frase, font=font, fill="black")
                            canvas.text((pos_x, pos_y), frase, font=font, fill=cor_texto)
                            
                            nome_frame = f"frame_temp_{i}.png"
                            img_frame.save(nome_frame)
                            arquivos_para_limpar.append(nome_frame)
                            
                            clip_img = ImageClip(nome_frame).set_duration(duracao_frase)
                            clips_de_video.append(clip_img)
                            
                        video_final_sem_audio = concatenate_videoclips(clips_de_video, method="compose")
                    
                    else:
                        video_final_sem_audio = ImageClip("fundo_final.png").set_duration(duracao_audio)

                with st.spinner("🎬 Juntando tudo no MP4 final..."):
                    audio_clip = AudioFileClip(audio_final_path)
                    
                    video_final = video_final_sem_audio.set_audio(audio_clip)
                    
                    video_final.write_videofile(
                        "video_final_tiktok.mp4", fps=24, codec="libx264", 
                        audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                    )
                
                minutos = int(duracao_audio // 60)
                segundos = int(duracao_audio % 60)
                
                st.success(f"🎉 VÍDEO COMPLETADO! Duração: {minutos}m {segundos}s.")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR MEU VÍDEO VIRAL",
                        data=file,
                        file_name="video_viral.mp4",
                        mime="video/mp4"
                    )
                
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
