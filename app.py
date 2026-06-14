import streamlit as st
import os
import requests
import math
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, CompositeVideoClip

st.set_page_config(page_title="Super Gerador TikTok Grátis", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos Inteligente")
st.markdown("Crie vídeos com imagens proporcionais e legendas que aparecem junto com a voz!")

# Garante que a API Key existe nos Secrets do Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: 3 curiosidades sobre o espaço")
    
    objetivo_video = st.selectbox(
        "Qual o Objetivo/Estilo do Vídeo?",
        (
            "Dica / Educacional (Focado em ensinar e agregar valor)", 
            "Conselho / Motivacional (Focado em reflexão e engajamento)", 
            "Curiosidade (Focado em prender a atenção com fatos)", 
            "Venda / Conversão (Focado em direcionar para o link na bio)"
        )
    )
    
    imagem_carregada = st.file_uploader("Suba sua imagem de fundo (.png ou .jpg)", type=["png", "jpg"])
    
    st.markdown("---")
    st.subheader("🎨 Customização das Legendas")
    
    # 📍 NOVO: ESCOLHA DE POSIÇÃO DO TEXTO
    posicao_texto = st.radio(
        "Onde a legenda deve aparecer?",
        ("No Topo (Parte Superior)", "No Fundo (Parte Inferior)"),
        horizontal=True
    )
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Narração e Áudio")
    
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Apenas Música de Fundo", "Voz Narrada + Música de Fundo")
    )
    
    # 🎙️ NOVAS OPÇÕES DE VOZES E VELOCIDADE
    voz_escolhida = st.selectbox(
        "Escolha o Sotaque/Narrador da Voz:",
        (
            "Português (Brasil) - Voz Padrão", 
            "Português (Portugal) - Voz Europeia",
            "Português (Brasil) - Voz Mais Pausada"
        )
    )
    
    lang_code = "pt"
    tld_code = "pt" if "Portugal" in voz_escolhida else "com.br"
    velocidade_lenta = True if "Pausada" in voz_escolhida else False
    
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
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                if "Dica" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser puramente EDUCACIONAL e instrutivo, focado em dar dicas práticas passo a passo. NÃO tente vender nada, NÃO fale sobre comprar e NÃO mencione 'link na bio'."
                elif "Conselho" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser de CONSELHO ou MOTIVACIONAL, com um tom reflexivo e inspirador. NÃO mencione vendas ou links."
                elif "Curiosidade" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser focado em CURIOSIDADE. Comece com um gancho forte (ex: 'Você sabia que...'). NÃO mencione vendas."
                else:
                    instrucao_estilo = "O estilo deve ser focado em VENDA e CONVERSÃO direta. Faça um gancho, apresente o problema e mande clicar no link da bio."

                prompt = f"Escreva um texto curto composto por EXATAMENTE 3 ou 4 frases curtas e diretas para o TikTok sobre o tema: '{tema}'. {instrucao_estilo} Tamanho máximo de 130 caracteres no total. Retorne APENAS o texto puro do roteiro corrido, sem indicações de cena, sem aspas, sem asteriscos e sem parênteses."
                
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

                # ---- MOTOR DE ÁUDIO (gTTS) ----
                def criar_audio_gtts(texto, caminho_saida, lang, tld, slow):
                    try:
                        tts = gTTS(text=texto, lang=lang, tld=tld, slow=slow)
                        tts.save(caminho_saida)
                        return True
                    except Exception as e:
                        st.error(f"Erro ao gerar áudio: {e}")
                        return False

                # ---- CRIAÇÃO DO ÁUDIO ----
                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner("🎙️ Gerando narração..."):
                        if criar_audio_gtts(texto_do_video, audio_final_path, lang_code, tld_code, velocidade_lenta):
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
                        if criar_audio_gtts(texto_do_video, "voz_temp.mp3", lang_code, tld_code, velocidade_lenta):
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
                
                # ---- 🎨 NOVO: PROCESSAMENTO DA IMAGEM PROPORCIONAL ----
                with st.spinner("🎨 Ajustando imagem proporcional e centralizada..."):
                    # Criamos um fundo preto padrão vertical de celular (1080x1920)
                    fundo_preto = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
                    
                    # Carrega a imagem do usuário e redimensiona proporcionalmente sem distorcer
                    img_usuario = Image.open(imagem_carregada).convert("RGBA")
                    largura_original, altura_original = img_usuario.size
                    
                    # Define que a imagem vai ocupar no máximo 1080 de largura e 1100 de altura no centro
                    max_largura, max_altura = 1080, 1100
                    proporcao = min(max_largura / largura_original, max_altura / altura_original)
                    nova_largura = int(largura_original * proporcao)
                    nova_altura = int(altura_original * proporcao)
                    
                    img_redimensionada = img_usuario.resize((nova_largura, nova_altura))
                    
                    # Cola a imagem exatamente no centro do fundo preto
                    pos_x = (1080 - nova_largura) // 2
                    pos_y = (1920 - nova_altura) // 2
                    fundo_preto.paste(img_redimensionada, (pos_x, pos_y), img_redimensionada)
                    fundo_preto.save("fundo_proporcional.png")
                    arquivos_para_limpar.append("fundo_proporcional.png")

                # ---- ✍️ NOVO: GERADOR DE FRASES SINCRONIZADAS DINÂMICAS ----
                with st.spinner("✍️ Sincronizando frases da legenda com o tempo..."):
                    # Divide o texto do vídeo em frases/blocos baseados em pontos ou vírgulas
                    frases = [f.strip() for f in texto_do_video.replace(".", ".|").replace(",", ",|").split("|") if f.strip()]
                    if not frases:
                        frases = [texto_do_video]
                        
                    tempo_por_frase = duracao_video / len(frases)
                    lista_clips_legendas = []
                    
                    # Tenta carregar uma fonte grande e robusta do sistema
                    try: font = ImageFont.truetype("LiberationSans-Bold.ttf", 60)
                    except IOError:
                        try: font = ImageFont.truetype("Arial.ttf", 60)
                        except IOError: font = ImageFont.load_default()

                    # Cria um clip transparente de legenda para cada trecho do áudio
                    for i, frase in enumerate(frases):
                        img_transparente = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
                        canvas = ImageDraw.Draw(img_transparente)
                        
                        # Centralização horizontal automática do texto grande
                        x_text = (1080 - (len(frase) * 30)) // 2
                        if x_text < 50: x_text = 50
                        
                        # Define a altura baseado na escolha do usuário (Topo ou Fundo) sem bater na imagem central
                        y_text = 200 if "Topo" in posicao_texto else 1650
                        
                        # Aplica contorno preto marcante
                        for adj_x in [-3, 0, 3]:
                            for adj_y in [-3, 0, 3]:
                                canvas.text((x_text + adj_x, y_text + adj_y), frase, font=font, fill="black")
                        # Texto branco por cima
                        canvas.text((x_text, y_text), frase, font=font, fill="white")
                        
                        nome_img_temp = f"legenda_{i}.png"
                        img_transparente.save(nome_img_temp)
                        arquivos_para_limpar.append(nome_img_temp)
                        
                        # Define o momento exato em que a frase entra e sai da tela
                        inicio_tempo = i * tempo_por_frase
                        fim_tempo = (i + 1) * tempo_por_frase
                        
                        clip_legenda = (ImageClip(nome_img_temp)
                                       .set_start(inicio_tempo)
                                       .set_end(fim_tempo))
                        lista_clips_legendas.append(clip_legenda)

                # ---- RENDERIZANDO O VÍDEO FINAL CINEMATOGRÁFICO ----
                with st.spinner("🎬 Juntando imagem, áudio e legendas dinâmicas..."):
                    with AudioFileClip(audio_final_path) as audio_clip:
                        if tipo_audio == "Apenas Música de Fundo":
                            audio_clip = audio_clip.subclip(0, duracao_video)
                            
                        # Cria o clip base com a foto centralizada proporcionalmente
                        clip_fundo_base = ImageClip("fundo_proporcional.png").set_duration(duracao_video)
                        
                        # Junta a imagem de fundo estática com todas as camadas de texto dinâmicas
                        video_com_legendas = CompositeVideoClip([clip_fundo_base] + lista_clips_legendas)
                        video_final = video_com_legendas.set_audio(audio_clip)
                        
                        video_final.write_videofile(
                            "video_final_tiktok.mp4", fps=24, codec="libx264", 
                            audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                        )
                
                st.success("🎉 SEU VÍDEO COMPLETO E SINCRONIZADO FICOU PRONTO!")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 DOWNLOAD DO VÍDEO",
                        data=file,
                        file_name="video_tiktok_perfeito.mp4",
                        mime="video/mp4"
                    )
                
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
