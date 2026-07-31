import streamlit as st
import os
import requests
import asyncio
import edge_tts 
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip
import textwrap

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos (Fundo Fixo + Anti-Gaguejo)")
st.markdown("Configure o estilo do seu vídeo abaixo e deixe a IA trabalhar.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: A rivalidade entre Senna e Prost")
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
        communicate = edge_tts.Communicate(texto, voz, rate="-10%")
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
        with st.spinner("🤖 Google Gemini criando o roteiro limpo..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                tamanho_max = "cerca de 135 a 145 palavras" if "Voz" in tipo_audio else "máximo 140 caracteres"
                
                prompt = f"""Escreva um roteiro para TikTok/Shorts sobre o tema: '{tema}'.
                O tom deve ser EXALTADO, PROVOCATIVO e um pouco POLÊMICO para prender a atenção e gerar debate na audiência.
                REGRA OBRIGATÓRIA 1: O roteiro DEVE terminar com uma afirmação forte, absoluta e controversa que deixe a audiência revoltada ou com muita vontade de debater. NÃO peça para curtir, compartilhar ou comentar. Apenas jogue a bomba e termine o vídeo abruptamente.
                REGRA OBRIGATÓRIA 2: O texto total deve ter {tamanho_max}.
                REGRA OBRIGATÓRIA 3: NUNCA repita palavras, sílabas ou crie gaguejos no final das frases ou nomes (como 'leclercler'). Escreva de forma limpa, natural e correta até o último caractere.
                Retorne APENAS o texto puro, sem indicações de cena, sem aspas, sem asteriscos, sem hashtags e sem parênteses."""
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '')
                
                # Limpeza extra de segurança para remover qualquer duplicação de palavras/sílabas no final
                palavras = texto_do_video.split()
                if len(palavras) > 1:
                    ultima = palavras[-1].lower()
                    penultima = palavras[-2].lower()
                    # Se a última palavra for igual à penúltima ou contiver repetição de sílaba colada
                    if ultima == penultima or (len(ultima) > 4 and ultima.startswith(penultima[:3])):
                        palavras.pop()
                        texto_do_video = " ".join(palavras)
                
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

                with st.spinner("🎨 Posicionando o texto na tela..."):
                    imagem_fundo_base = Image.open(imagem_carregada).resize((1080, 1920))
                    
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

                    img_frame = imagem_fundo_base.copy()
                    canvas = ImageDraw.Draw(img_frame)
                    
                    linhas_roteiro = textwrap.wrap(texto_do_video, width=42)
                    
                    # Posição ideal na tela (y_inicial = 820)
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

                    nome_imagem_estatica = "fundo_com_texto_fixo.png"
                    img_frame.save(nome_imagem_estatica)
                    arquivos_para_limpar.append(nome_imagem_estatica)
                    
                    video_final_sem_audio = ImageClip(nome_imagem_estatica).set_duration(duracao_audio)

                with st.spinner("🎬 Renderizando vídeo final..."):
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
