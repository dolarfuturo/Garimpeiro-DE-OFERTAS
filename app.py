import streamlit as st
import os
import requests
import random
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip

st.set_page_config(page_title="Super Gerador TikTok Premium", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos 100% Automática")
st.markdown("Digite apenas o tema! O robô criará o roteiro, buscará a imagem oficial e fará a narração sozinho.")

# Garante que as API Keys existem nos Secrets do Streamlit
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    pexels_key = st.secrets["PEXELS_API_KEY"]
except Exception:
    st.error("❌ Chaves API não encontradas nos Secrets! Certifique-se de configurar 'GEMINI_API_KEY' e 'PEXELS_API_KEY'.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: Curiosidades sobre o espaço ou Como investir sendo jovem")
    
    objetivo_video = st.selectbox(
        "Qual o Objetivo/Estilo do Vídeo?",
        (
            "Dica / Educacional (Focado em ensinar e agregar valor)", 
            "Conselho / Motivacional (Focado em reflexão e engajamento)", 
            "Curiosidade (Focado em prender a atenção com fatos)", 
            "Venda / Conversão (Focado em fazer chamada de ação)"
        )
    )
    
    st.markdown("---")
    st.subheader("🎨 Posição das Legendas")
    posicao_texto = st.radio(
        "Onde a legenda deve aparecer?",
        ("No Topo (Parte Superior)", "No Fundo (Parte Inferior)"),
        horizontal=True
    )
    
    st.markdown("---")
    st.subheader("🎵 Configurações de Narração")
    tipo_audio = st.radio(
        "Como quer o áudio do vídeo?",
        ("Apenas Voz Narrada", "Voz Narrada + Música de Fundo")
    )
    
    voz_escolhida = st.selectbox(
        "Escolha o Estilo do Narrador:",
        (
            "Fábio (Voz Dinâmica - Perfil Finanças/Vendas)", 
            "Donato (Voz Firme - Perfil Comercial)",
            "Francisca (Voz Suave - Perfil Educacional)",
            "Antônio (Voz Pausada - Perfil Motivacional)"
        )
    )
    
    if "Fábio" in voz_escolhida:
        lang_code, tld_code, velocidade_lenta = "pt", "com.br", False
    elif "Donato" in voz_escolhida:
        lang_code, tld_code, velocidade_lenta = "pt", "com.br", False
    elif "Francisca" in voz_escolhida:
        lang_code, tld_code, velocidade_lenta = "pt", "pt", False
    else:
        lang_code, tld_code, velocidade_lenta = "pt", "com.br", True
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR VÍDEO COMPLETO DO ZERO")

if botao_gerar:
    if not tema:
        st.error("❌ Por favor, digite um tema para o seu vídeo!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        status = st.empty()
        arquivos_para_limpar = []
        
        try:
            # ---------------- STEP 1: GERAR ROTEIRO OTIMIZADO ----------------
            status.info("🤖 1/5 | Google Gemini escrevendo roteiro fluido...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            headers = {'Content-Type': 'application/json'}
            
            if "Dica" in objetivo_video:
                instrucao_estilo = "O estilo deve ser EDUCACIONAL. Forneça parágrafos corridos e contínuos. SEM tópicos, SEM aspas e sem links."
            elif "Conselho" in objetivo_video:
                instrucao_estilo = "O estilo deve ser um CONSELHO profundo e motivacional. Crie parágrafos reflexivos e contínuos."
            elif "Curiosidade" in objetivo_video:
                instrucao_estilo = "O estilo deve ser focado em CURIOSIDADES SURPREENDENTES em formato narrativo corrido."
            else:
                instrucao_estilo = "O estilo deve ser focado em VENDAS. Explique o problema, gere desejo e direcione para a ação rápida."

            prompt = (f"Escreva um roteiro narrativo completo, longo e corrido para um vídeo de 1 minuto no TikTok sobre o tema: '{tema}'. "
                      f"{instrucao_estilo} O texto deve conter exatamente entre 110 e 125 palavras. "
                      f"Retorne APENAS o texto puro sem títulos, sem indicações de cena, sem aspas, sem R$ e sem asteriscos.")
            
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, headers=headers, json=payload)
            response_json = response.json()
            
            if response.status_code != 200:
                st.error(f"Erro na API do Google: {response_json.get('error', {}).get('message', 'Erro desconhecido')}")
                st.stop()
            
            texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
            texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '').replace("- ", "")
            st.info(f"📜 **Roteiro Gerado:** {texto_do_video}")
            
            # ---------------- STEP 2: AUDIO NARRADO ----------------
            audio_final_path = "audio_gerado_final.mp3"
            status.info("🎙️ 2/5 | Gerando arquivo de voz humanizada...")
            tts = gTTS(text=texto_do_video, lang=lang_code, tld=tld_code, slow=velocidade_lenta)
            tts.save(audio_final_path)
            arquivos_para_limpar.append(audio_final_path)
            
            with AudioFileClip(audio_final_path) as audio_clip_real:
                duracao_video = audio_clip_real.duration

            if "Música" in tipo_audio:
                status.info("🎵 Mixando faixa de áudio secundária...")
                with open("musica_temp.mp3", "wb") as f:
                    f.write(musica_carregada.getbuffer())
                arquivos_para_limpar.append("musica_temp.mp3")
                
                os.system(f'ffmpeg -y -i {audio_final_path} -stream_loop -1 -i musica_temp.mp3 -filter_complex "[1:a]volume=0.12[bg];[0:a][bg]amix=inputs=2:duration=first" -c:a mp3 mix_final.mp3 >/dev/null 2>&1')
                audio_final_path = "mix_final.mp3"
                arquivos_para_limpar.append("mix_final.mp3")

            # ---------------- STEP 3: BUSCA ESTÁVEL DE IMAGEM (PEXELS API) ----------------
            status.info("🖼️ 3/5 | Buscando imagem oficial HD alinhada ao tema...")
            
            palavra_busca = tema.split()[0] if len(tema.split()) > 0 else "finance"
            headers_pexels = {"Authorization": pexels_key}
            url_pexels = f"https://api.pexels.com/v1/search?query={palavra_busca}&per_page=5&orientation=portrait"
            
            img_salva = False
            try:
                res_p = requests.get(url_pexels, headers=headers_pexels, timeout=10)
                if res_p.status_code == 200:
                    dados_p = res_p.json()
                    if dados_p.get("photos"):
                        # Escolhe uma foto aleatória dentre as 5 encontradas para dar variedade
                        foto_url = random.choice(dados_p["photos"])["src"]["large2x"]
                        img_data = requests.get(foto_url, timeout=10).content
                        with open("imagem_baixada.jpg", "wb") as f:
                            f.write(img_data)
                        img_salva = True
            except:
                pass

            if not img_salva:
                # Fallback seguro caso dê qualquer erro de conexão externa
                img_fallback = Image.new("RGBA", (1080, 1050), (20, 25, 35, 255))
                img_fallback.save("imagem_baixada.jpg")

            arquivos_para_limpar.append("imagem_baixada.jpg")

            # Montagem do layout vertical TikTok (1080x1920)
            fundo_preto = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
            img_usuario = Image.open("imagem_baixada.jpg").convert("RGBA")
            
            largura_orig, altura_orig = img_usuario.size
            proporcao = min(1080 / largura_orig, 1050 / altura_orig)
            nova_largura = int(largura_orig * proporcao)
            nova_altura = int(altura_orig * proporcao)
            
            img_redimensionada = img_usuario.resize((nova_largura, nova_altura))
            pos_x = (1080 - nova_largura) // 2
            pos_y = (1920 - nova_altura) // 2
            
            fundo_preto.paste(img_redimensionada, (pos_x, pos_y), img_redimensionada)
            fundo_preto.save("fundo_proporcional.png")
            arquivos_para_limpar.append("fundo_proporcional.png")

            # ---------------- STEP 4: GERAR LEGENDAS ----------------
            status.info("✍️ 4/5 | Fatiando blocos rápidos de legendas...")
            frases_brutas = [f.strip() for f in texto_do_video.replace(".", "|").replace("!", "|").replace("?", "|").split("|") if f.strip()]
            
            blocos_legendas = []
            bloco_atual = ""
            for f in frases_brutas:
                if len(bloco_atual + " " + f) < 55:
                    bloco_atual = f"{bloco_atual} {f}".strip()
                else:
                    if bloco_atual: blocos_legendas.append(bloco_atual)
                    bloco_atual = f
            if bloco_atual: blocos_legendas.append(bloco_atual)
            
            tempo_por_bloco = duracao_video / len(blocos_legendas)
            lista_clips_legendas = []

            for idx, trecho in enumerate(blocos_legendas):
                palavras_trecho = trecho.split()
                linhas_trecho = []
                linha_aux = ""
                for p in palavras_trecho:
                    if len(linha_aux + " " + p) < 16:
                        linha_aux = f"{linha_aux} {p}".strip()
                    else:
                        linhas_trecho.append(linha_aux)
                        linha_aux = p
                if App_aux := linha_aux: linhas_trecho.append(App_aux)
                
                img_texto = Image.new("RGBA", (1080, 400), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img_texto)
                
                y_local = 20
                for linha in linhas_trecho:
                    if linha:
                        x_base = (1080 - (len(linha) * 29)) // 2
                        if x_base < 40: x_base = 40
                        
                        largura_box = len(linha) * 32
                        draw.rectangle([x_base - 15, y_local - 5, x_base + largura_box + 15, y_local + 75], fill=(0,0,0,170))
                        
                        for ox in [-2, -1, 1, 2]:
                            for oy in [-2, -1, 1, 2]:
                                draw.text((x_base + ox, y_local + oy), linha, fill=(0,0,0,255))
                        
                        draw.text((x_base, y_local), linha, fill=(255, 234, 0, 255))
                        y_local += 80
                
                nome_legenda_file = f"layer_{idx}.png"
                img_texto.save(nome_legenda_file)
                arquivos_para_limpar.append(nome_legenda_file)
                
                eixo_y_final = 150 if "Topo" in posicao_texto else 1450
                
                clip_text = (ImageClip(nome_legenda_file)
                            .set_start(idx * tempo_por_bloco)
                            .set_end((idx + 1) * tempo_por_bloco)
                            .set_position((0, eixo_y_final)))
                lista_clips_legendas.append(clip_text)

            # ---------------- STEP 5: COMPILAR VÍDEO ----------------
            status.info("🎬 5/5 | Montagem final super veloz ativa...")
            clip_fundo_base = ImageClip("fundo_proporcional.png").set_duration(duracao_video)
            video_com_legendas = CompositeVideoClip([clip_fundo_base] + lista_clips_legendas, size=(1080, 1920))
            
            video_final = video_com_legendas.set_audio(AudioFileClip(audio_final_path))
            
            video_final.write_videofile(
                "video_final_tiktok.mp4", fps=24, codec="libx264", 
                audio_codec="aac", preset="ultrafast", threads=4, 
                logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"]
            )
            
            video_final.close()
            clip_fundo_base.close()
            
            status.empty()
            st.success(f"🎉 SEU VÍDEO COMPLETO E AUTOMÁTICO FOI GERADO! Duração: {int(duracao_video)} segundos.")
            
            with open("video_final_tiktok.mp4", "rb") as file:
                st.download_button(
                    label="📥 DOWNLOAD DO VÍDEO PRONTO",
                    data=file,
                    file_name="video_automatico.mp4",
                    mime="video/mp4"
                )
            
            arquivos_para_limpar.append("video_final_tiktok.mp4")
            for arquivo in arquivos_para_limpar:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    
        except Exception as e:
            st.error(f"Erro inesperado no sistema: {e}")
