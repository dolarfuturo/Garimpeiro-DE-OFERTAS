import streamlit as st
import os
import requests
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, CompositeVideoClip

st.set_page_config(page_title="Super Gerador TikTok Premium", page_icon="🎬", layout="centered")

st.title("🎬 Fábrica de Vídeos Longos (Vozes Realistas)")
st.markdown("Gere vídeos educativos de ~1 minuto com vozes neurais humanas, imagens proporcionais e letras gigantes.")

# Garante que a API Key existe nos Secrets do Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("❌ Chave API não encontrada nos Secrets do Streamlit! Verifique se configurou 'GEMINI_API_KEY' corretamente.")
    st.stop()

with st.form(key="gerador_video"):
    tema = st.text_input("Qual o tema do vídeo?", placeholder="Ex: 5 passos para organizar suas finanças pessoais hoje")
    
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
        ("Apenas Voz Narrada", "Apenas Música de Fundo", "Voz Narrada + Música de Fundo")
    )
    
    # 🎙️ VOZES NEURAIS REAIS COMPATÍVEIS COM O MOTOR AVANÇADO
    voz_escolhida = st.selectbox(
        "Escolha o Narrador (Vozes Humanas Reais):",
        (
            "pt-BR-FabioNeural (Masculino - Finanças)", 
            "pt-BR-DonatoNeural (Masculino - Comercial)",
            "pt-BR-FranciscaNeural (Feminino - Educacional)",
            "pt-BR-AntonioNeural (Masculino - Motivacional)"
        )
    )
    
    # Extrai o código limpo da voz para enviar ao servidor de áudio
    voice_clean = voz_escolhida.split(" ")[0]
    
    musica_carregada = st.file_uploader("Suba a música de fundo (.mp3) - Opcional se for Apenas Voz", type=["mp3"])
    
    st.markdown("---")
    botao_gerar = st.form_submit_button(label="🚀 GERAR VÍDEO COMPLETO (~1 MINUTO)")

if botao_gerar:
    if not tema or not imagem_carregada:
        st.error("❌ Por favor, preencha o Tema e envie a Imagem!")
    elif "Música" in tipo_audio and not musica_carregada:
        st.error("❌ Você selecionou uma opção com música, mas não enviou o arquivo .mp3!")
    else:
        with st.spinner("🤖 Google Gemini escrevendo um roteiro completo de 1 minuto..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                
                if "Dica" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser EDUCACIONAL, aprofundado e rico em conteúdo. Dê dicas úteis detalhadas divididas em tópicos ou parágrafos fluídos. NÃO cite vendas, NÃO fale em comprar e JAMAIS use a palavra 'bio' ou links."
                elif "Conselho" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser um CONSELHO profundo, com tom maduro, sábio e focado em desenvolvimento pessoal. Crie parágrafos reflexivos e impactantes."
                elif "Curiosidade" in objetivo_video:
                    instrucao_estilo = "O estilo deve ser focado em CURIOSIDADES SURPREENDENTES. Explique a história ou a ciência por trás do tema detalhadamente para manter o usuário assistindo até o fim."
                else:
                    instrucao_estilo = "O estilo deve ser focado em VENDAS. Explique o problema, gere desejo e no final faça uma chamada de ação forte para clicar no link da bio."

                prompt = (f"Escreva um roteiro narrativo completo, longo e fluído para um vídeo de 1 minuto no TikTok sobre o tema: '{tema}'. "
                          f"{instrucao_estilo} O texto deve conter entre 115 e 145 palavras no total, dividido de forma natural. "
                          f"Retorne APENAS o texto corrido que o narrador vai falar. Não inclua títulos, não divida por cenas, sem aspas, sem asteriscos e sem parênteses.")
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                if response.status_code != 200:
                    st.error(f"Erro na API do Google: {response_json.get('error', {}).get('message', 'Erro desconhecido')}")
                    st.stop()
                
                texto_do_video = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                texto_do_video = texto_do_video.replace("**", "").replace("*", "").replace('"', '').replace("- ", "")
                st.info(f"📜 **Roteiro Gerado pelo Gemini:**\n\n{texto_do_video}")
                
                audio_final_path = "audio_gerado_final.mp3"
                arquivos_para_limpar = []

                # ---- MOTOR DE ÁUDIO NEURAL REALISTA (EDGE-TTS) ----
                async def gerar_audio_neural(text, voice_name, output_path):
                    communicate = edge_tts.Communicate(text, voice_name)
                    await communicate.save(output_path)

                def rodar_audio(text, voice_name, output_path):
                    try:
                        asyncio.run(gerar_audio_neural(text, voice_name, output_path))
                        return True
                    except Exception as e:
                        st.error(f"Erro ao gerar áudio neural: {e}")
                        return False

                # ---- PROCESSAMENTO DE ÁUDIO ----
                if tipo_audio == "Apenas Voz Narrada":
                    with st.spinner(f"🎙️ Clonando e gravando a voz real de {voice_clean}..."):
                        if rodar_audio(texto_do_video, voice_clean, audio_final_path):
                            arquivos_para_limpar.append(audio_final_path)
                            duracao_video = AudioFileClip(audio_final_path).duration
                        else: st.stop()
                
                elif tipo_audio == "Apenas Música de Fundo":
                    with st.spinner("🎵 Configurando música de fundo..."):
                        with open("musica_temp.mp3", "wb") as f:
                            f.write(musica_carregada.getbuffer())
                        arquivos_para_limpar.append("musica_temp.mp3")
                        audio_final_path = "musica_temp.mp3"
                        duracao_video = min(AudioFileClip(audio_final_path).duration, 60)
                
                elif tipo_audio == "Voz Narrada + Música de Fundo":
                    with st.spinner(f"🎛️ Mixando voz real de {voice_clean} + Música..."):
                        if rodar_audio(texto_do_video, voice_clean, "voz_temp.mp3"):
                            arquivos_para_limpar.append("voz_temp.mp3")
                            with open("musica_temp.mp3", "wb") as f:
                                f.write(musica_carregada.getbuffer())
                            arquivos_para_limpar.append("musica_temp.mp3")
                            
                            v_clip = AudioFileClip("voz_temp.mp3")
                            duracao_video = v_clip.duration
                            
                            m_clip = AudioFileClip("musica_temp.mp3").volumex(0.12)
                            if m_clip.duration < duracao_video:
                                m_clip = m_clip.loop(duration=duracao_video)
                            else:
                                m_clip = m_clip.subclip(0, duracao_video)
                            
                            mixed_audio = CompositeAudioClip([v_clip, m_clip])
                            mixed_audio.write_audiofile("mix_final.mp3", logger=None)
                            arquivos_para_limpar.append("mix_final.mp3")
                            audio_final_path = "mix_final.mp3"
                        else: st.stop()
                
                # ---- 🎨 DESIGN DE IMAGEM PROPORCIONAL CENTRALIZADA ----
                with st.spinner("🎨 Redimensionando imagem de forma proporcional..."):
                    fundo_preto = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
                    img_usuario = Image.open(imagem_carregada).convert("RGBA")
                    
                    largura_orig, altura_orig = img_usuario.size
                    max_largura, max_altura = 1080, 1000 
                    
                    proporcao = min(max_largura / largura_orig, max_altura / altura_orig)
                    nova_largura = int(largura_orig * proporcao)
                    nova_altura = int(altura_orig * proporcao)
                    
                    img_redimensionada = img_usuario.resize((nova_largura, nova_altura))
                    pos_x = (1080 - nova_largura) // 2
                    pos_y = (1920 - nova_altura) // 2
                    
                    fundo_preto.paste(img_redimensionada, (pos_x, pos_y), img_redimensionada)
                    fundo_preto.save("fundo_proporcional.png")
                    arquivos_para_limpar.append("fundo_proporcional.png")

                # ---- ✍️ GERADOR DE LEGENDAS GIGANTES CORRIGIDO ----
                with st.spinner("✍️ Desenhando blocos de legendas ultra visíveis..."):
                    frases_brutas = [f.strip() for f in texto_do_video.replace(".", "|").replace("!", "|").replace("?", "|").split("|") if f.strip()]
                    
                    blocos_legendas = []
                    bloco_atual = ""
                    for f in frases_brutas:
                        if len(bloco_atual + " " + f) < 65:
                            bloco_atual = f"{bloco_atual} {f}".strip()
                        else:
                            if bloco_atual: blocos_legendas.append(bloco_atual)
                            bloco_atual = f
                    if bloco_atual: blocos_legendas.append(bloco_atual)
                    
                    tempo_por_bloco = duracao_video / len(blocos_legendas)
                    lista_clips_legendas = []

                    for idx, trecho in enumerate(blocos_legendas):
                        img_texto = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(img_texto)
                        
                        palavras_trecho = trecho.split()
                        linhas_trecho = []
                        linha_aux = ""
                        for p in palavras_trecho:
                            if len(linha_aux + " " + p) < 18:
                                linha_aux = f"{linha_aux} {p}".strip()
                            else:
                                linhas_trecho.append(linha_aux)
                                linha_aux = p
                        if linha_aux: linhas_trecho.append(linha_aux)
                        
                        y_base = 180 if "Topo" in posicao_texto else 1500
                        
                        for linha in linhas_trecho:
                            if linha:
                                tam_letra_aprox = 58
                                x_base = (1080 - (len(linha) * (tam_letra_aprox // 2))) // 2
                                if x_base < 40: x_base = 40
                                
                                largura_box = len(linha) * 32
                                draw.rectangle([x_base - 20, y_base - 10, x_base + largura_box + 20, y_base + 80], fill=(0,0,0,180))
                                
                                # CORREÇÃO CRÍTICA DO ERRO AQUI: Passado o argumento 'linha' em todos os desenhos do contorno
                                for ox in [-2, -1, 0, 1, 2]:
                                    for oy in [-2, -1, 0, 1, 2]:
                                        draw.text((x_base + ox, y_base + oy), linha, fill=(0,0,0,255))
                                
                                draw.text((x_base, y_base), linha, fill=(255, 234, 0, 255))
                                y_base += 85
                        
                        nome_legenda_file = f"layer_{idx}.png"
                        img_texto.save(nome_legenda_file)
                        arquivos_para_limpar.append(nome_legenda_file)
                        
                        start_f = idx * tempo_por_bloco
                        end_f = (idx + 1) * tempo_por_bloco
                        
                        clip_text = (ImageClip(nome_legenda_file)
                                    .set_start(start_f)
                                    .set_end(end_f))
                        lista_clips_legendas.append(clip_text)

                # ---- COMPOSIÇÃO E EXPORTAÇÃO FINAL DO VÍDEO COMPLETO ----
                with st.spinner("🎬 Renderizando arquivo final..."):
                    with AudioFileClip(audio_final_path) as audio_clip:
                        clip_fundo_base = ImageClip("fundo_proporcional.png").set_duration(duracao_video)
                        
                        video_com_legendas = CompositeVideoClip([clip_fundo_base] + lista_clips_legendas)
                        video_final = video_com_legendas.set_audio(audio_clip)
                        
                        video_final.write_videofile(
                            "video_final_tiktok.mp4", fps=24, codec="libx264", 
                            audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None
                        )
                
                st.success(f"🎉 VÍDEO DE 1 MINUTO GERADO COM SUCESSO! Tempo final: {int(duracao_video)} segundos.")
                
                with open("video_final_tiktok.mp4", "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR MEU VÍDEO DE 1 MINUTO",
                        data=file,
                        file_name="video_educativo_longo.mp4",
                        mime="video/mp4"
                    )
                
                arquivos_para_limpar.append("video_final_tiktok.mp4")
                for arquivo in arquivos_para_limpar:
                    if os.path.exists(arquivo):
                        os.remove(arquivo)
                        
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
