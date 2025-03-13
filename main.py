from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from typing import Literal
from TTS.api import TTS
import numpy as np
import soundfile as sf
import torch
import io
import tempfile

# Cria a aplicação FastAPI
app = FastAPI()

# Endpoint para gerar áudio a partir de texto com voz clonada
@app.post("/generate_audio/")
async def generate_audio(
    text: str,
    language: Literal["en", "pt", "es"] = "pt",
    voice_to_be_cloned: UploadFile = File(...)
):
    # Define o dispositivo (GPU ou CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Inicializa o modelo TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

    # Cria um arquivo temporário para armazenar o áudio enviado
    with tempfile.NamedTemporaryFile(suffix=".wav") as temp_clone_voice:
        # Escreve o conteúdo do arquivo enviado no arquivo temporário
        temp_clone_voice.write(await voice_to_be_cloned.read())
        temp_clone_voice.seek(0)

        # Gera o áudio usando a voz clonada
        wav = tts.tts(
            text=text,
            speaker_wav=temp_clone_voice.name,
            language=language
        )

    # Converte a lista de áudio para um array NumPy
    wav_np = np.array(wav, dtype=np.float32)

    # Cria um buffer em memória para o áudio
    audio_buffer = io.BytesIO()
    sf.write(audio_buffer, wav_np, samplerate=22050, format='WAV')
    audio_buffer.seek(0)

    # Retorna o áudio como uma resposta de streaming
    return StreamingResponse(audio_buffer, media_type="audio/wav")
