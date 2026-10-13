import streamlit as st
import asyncio
import requests
import whisper
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, afx
import os

# Configuración de interfaz
st.set_page_config(page_title="ClipShort Pro AI", page_icon="🎬", layout="centered")
st.title("🎬 ClipShort Pro AI")
st.subheader("Generador de Videos Verticales Gratuito")

# --- GENERADOR DE GUION LIBRE Y SIN CLAVES ---
def generar_guion_libre(tema):
    url = "https://pollinations.ai"
    prompt = f"Escribe un guion dinámico, entretenido y viral para un video corto de TikTok sobre: {tema}. Debe durar unos 30 segundos de lectura rápida. No incluyas nombres de personajes, ni acotaciones entre paréntesis, ni introducciones secundarias. Devuelve únicamente el texto limpio que leerá el narrador en un solo párrafo largo."
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "openai-large"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
        
    return f"¿Sabías esto sobre {tema}? Es uno de los datos más increíbles y fascinantes del mundo que la mayoría de las personas desconoce por completo. Si te apasionan estos misterios, quédate hasta el final para descubrir todo su impacto."

# --- GENERADOR DE VOZ DE GOOGLE ---
def generar_voz(texto, idioma_config, archivo_audio="v_temp.mp3"):
    tts = gTTS(text=texto, lang=idioma_config, slow=False)
    tts.save(archivo_audio)
    return archivo_audio

# --- GENERADOR DE IMÁGENES CORREGIDO ---
def generar_imagen(prompt_visual, archivo_img="i_temp.jpg"):
    # Dirección web oficial corregida para evitar el NameResolutionError
    url = f"https://pollinations.ai{prompt_visual.replace(' ', '%20')}?width=1080&height=1920&enhanced=true"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(archivo_img, 'wb') as f:
                f.write(response.content)
            return archivo_img
    except Exception as e:
        st.error(f"Error al conectar con el servidor de imágenes: {e}")
    return None

def crear_subtitulos_clips(archivo_audio):
    model = whisper.load_model("base")
    result = model.transcribe(archivo_audio, language="es", word_timestamps=True)
    
    clips_texto = []
    for segment in result.get('segments', []):
        for word_info in segment.get('words', []):
            palabra = word_info['word'].strip().upper()
            start_time = word_info['start']
            end_time = word_info['end']
            duracion = end_time - start_time if (end_time - start_time) > 0 else 0.1
                
            txt_clip = (TextClip(palabra, fontsize=85, color='yellow', font='Arial-Bold',
                                 stroke_color='black', stroke_width=4, method='caption', 
                                 size=(880, None))
                        .set_start(start_time)
                        .set_duration(duracion)
                        .set_position(('center', 'center')))
            clips_texto.append(txt_clip)
    return clips_texto

# --- INTERFAZ DE USUARIO LIMPIA ---

st.markdown("### 🎛️ Configuración de tu Short")
tema_video = st.text_input("💡 ¿De qué quieres que hable el video?", placeholder="Ej: Curiosidades de los dinosaurios")

voces = {
    "🎙️ Voz en Español (Latinoamérica)": "es",
    "🎙️ Voz en Español (España)": "es",
}
voz_elegida = st.selectbox("🗣️ Elige el acento:", list(voces.keys()))

st.markdown("### 🎨 Estilo Visual y Música")
prompt_ia = st.text_input("🖼️ Estilo del fondo (En inglés funciona mejor):", placeholder="t-rex dinosaur cinematic hyperrealistic vertical 8k")
musica_subida = st.file_uploader("🎵 Sube música (.mp3) desde tu dispositivo (Opcional):", type=["mp3"])

# --- PROCESAMIENTO ---
if st.button("🚀 GENERAR VIDEO FULL"):
    if not tema_video or not prompt_ia:
        st.error("Por favor, completa el tema del video y el estilo visual del fondo.")
    else:
        with st.spinner("🤖 La IA está redactando el guion y compilando el Short..."):
            try:
                audio_path = "v_temp.mp3"
                img_path = "i_temp.jpg"
                video_final_path = "short_final.mp4"
                
                # Generación del guion sin usar claves
                guion = generar_guion_libre(tema_video)
                
                st.write("**📝 Guion redactado automáticamente:**")
                st.info(guion)
                
                # Generar voz estable con Google
                generar_voz(guion, voces[voz_elegida], audio_path)
                voz_clip = AudioFileClip(audio_path)
                
                if musica_subida is not None:
                    with open("m_temp.mp3", "wb") as f:
                        f.write(musica_subida.getbuffer())
                    musica_clip = AudioFileClip("m_temp.mp3")
                    if musica_clip.duration < voz_clip.duration:
                        musica_clip = afx.audio_loop(musica_clip, duration=voz_clip.duration)
                    else:
                        musica_clip = musica_clip.set_duration(voz_clip.duration)
                    musica_clip = musica_clip.volumex(0.12)
                    audio_final = CompositeAudioClip([voz_clip, musica_clip])
                else:
                    audio_final = voz_clip
                
                # Generar imagen de fondo corregida
                imagen_resultado = generar_imagen(prompt_ia, img_path)
                if not imagen_resultado:
                    st.error("No se pudo descargar la imagen de fondo. Intenta con otro estilo visual.")
                    st.stop()
                    
                fondo_clip = ImageClip(img_path).set_duration(voz_clip.duration)
                
                subtitulos = crear_subtitulos_clips(audio_path)
                
                video_final = CompositeVideoClip([fondo_clip] + subtitulos).set_audio(audio_final)
                video_final.write_videofile(video_final_path, fps=24, codec="libx264", audio_codec="aac")
                
                st.success("🎉 ¡Tu video se generó correctamente!")
                st.video(video_final_path)
                
                with open(video_final_path, "rb") as file:
                    st.download_button(label="📥 Guardar Video en la PC / Celular", data=file, file_name="short_ia.mp4", mime="video/mp4")
                
                voz_clip.close()
                if musica_subida:
                    musica_clip.close()
                    os.remove("m_temp.mp3")
                video_final.close()
                os.remove(audio_path)
                os.remove(img_path)
                
            except Exception as e:
                st.error(f"Error durante el procesamiento: {e}")


