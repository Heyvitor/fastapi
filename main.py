from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from gtts import gTTS
import io
import os
import logging
import base64

# Configurando o logging pra acompanhar o que acontece
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Criando nossa aplicação FastAPI
app = FastAPI()

# Função pra gerar o áudio e devolver ele de um jeito legal
def generate_audio_data(text: str, lang: str = 'pt', voice: str = 'normal'):
    """
    Pega um texto e transforma em áudio com gTTS, devolvendo o arquivo e o base64 pra usar depois.
    """
    try:
        # Se o usuário quer uma voz mais lenta, ajustamos aqui
        slow = True if voice == 'slow' else False
        
        # Adiciona umas pausas pra soar mais natural, como uma pessoa falando
        text_with_pauses = text.replace('.', '. ').replace(',', ', ')
        
        # Criamos o áudio com o gTTS
        tts = gTTS(text=text_with_pauses, lang=lang, slow=slow)
        audio_file = io.BytesIO()  # Um lugar temporário pra guardar o áudio
        tts.write_to_fp(audio_file)
        audio_file.seek(0)  # Volta pro começo pra gente usar

        # Transforma o áudio em base64 pra mandar pro front-end
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_file.seek(0)  # Volta de novo pro começo, pra garantir

        return audio_file, audio_base64

    except ValueError as ve:
        logging.error(f"Deu ruim com o idioma: {ve}")
        raise HTTPException(status_code=400, detail=f"O idioma '{lang}' não rolou. Detalhe: {ve}")
    except AssertionError as ae:
        logging.error(f"Texto vazio não dá né: {ae}")
        raise HTTPException(status_code=400, detail="Opa, precisa de texto pra gerar o áudio!")
    except Exception as e:
        logging.exception("Algo inesperado aconteceu:")
        raise HTTPException(status_code=500, detail=f"Deu um erro chato aqui: {e}")

# Endpoint pra gerar o áudio e mandar pro usuário
@app.post("/generate_audio/")
async def generate_audio_endpoint(
    text: str = Query(..., min_length=1), 
    lang: str = Query("pt", max_length=5), 
    voice: str = Query("normal")
):
    """
    Recebe o texto, idioma e tipo de voz, gera o áudio e devolve um JSON com o base64.
    """
    audio_file, audio_base64 = generate_audio_data(text, lang, voice)
    return JSONResponse(content={"audio_base64": audio_base64})

# Página inicial com um formulário simples e bonito
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Mostra uma página HTML pra usuário interagir e gerar o áudio.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Gerador de Áudio Simples</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #333; }
        button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
    <script>
        async function generateAudio() {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('langSelect').value;
            const voice = document.getElementById('voiceSelect').value;

            if (!text.trim()) {
                alert("Ei, coloca um texto aí pra eu transformar em áudio!");
                return;
            }

            try {
                const response = await fetch(`/generate_audio/?text=${encodeURIComponent(text)}&lang=${lang}&voice=${voice}`, {
                    method: 'POST',
                });

                if (response.ok) {
                    const data = await response.json();
                    const audioBase64 = data.audio_base64;

                    // Toca o áudio direto no navegador
                    const audio = new Audio('data:audio/mpeg;base64,' + audioBase64);
                    audio.play();
                } else {
                    alert("Ops, algo deu errado na geração do áudio!");
                    console.error("Erro:", await response.text());
                }
            } catch (error) {
                alert("Hmm, não consegui gerar o áudio. Vamos tentar de novo?");
                console.error("Erro na conexão:", error);
            }
        }
    </script>
</head>
<body>
    <h1>Transforme Texto em Áudio!</h1>
    <textarea id="textInput" placeholder="Escreva algo aqui..." rows="5" cols="50"></textarea><br><br>
    <label for="langSelect">Escolha o idioma:</label>
    <select id="langSelect">
        <option value="pt">Português (Brasil)</option>
        <option value="en">Inglês</option>
        <option value="es">Espanhol</option>
        <option value="fr">Francês</option>
        <option value="de">Alemão</option>
    </select><br><br>
    <label for="voiceSelect">Tipo de voz:</label>
    <select id="voiceSelect">
        <option value="normal">Normal</option>
        <option value="slow">Bem devagar</option>
    </select><br><br>
    <button onclick="generateAudio()">Gerar e Tocar Áudio</button>
</body>
</html>
    """

# Rodando tudo direitinho
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
