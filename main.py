from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import pyttsx3
import io
import logging
import base64
import os

# Configurando o logging pra gente ver o que tá acontecendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

def generate_audio_data(text: str, lang: str = 'pt-BR', voice: str = 'normal'):
    """
    Gera áudio com pyttsx3, tentando vozes de homem, mulher ou normal.
    """
    try:
        # Inicia o motor de fala
        engine = pyttsx3.init('espeak')  # Especifica o eSpeak explicitamente

        # Lista as vozes disponíveis
        voices = engine.getProperty('voices')
        if not voices:
            raise Exception("Nenhuma voz disponível. Instale o eSpeak ou outro sintetizador.")

        # Tenta configurar o idioma
        voice_set = False
        if 'pt' in lang.lower():
            for v in voices:
                if 'pt' in v.languages[0].lower():
                    engine.setProperty('voice', v.id)
                    voice_set = True
                    break
        if not voice_set:
            engine.setProperty('voice', voices[0].id)  # Usa a voz padrão se o idioma não for encontrado

        # Ajusta a voz com base na escolha
        if voice == 'man':
            engine.setProperty('voice', voices[0].id)  # Voz padrão, geralmente masculina no eSpeak
            engine.setProperty('rate', 150)  # Mais grave
        elif voice == 'woman':
            engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
            engine.setProperty('rate', 200)  # Mais aguda
        else:
            engine.setProperty('rate', 175)  # Normal

        # Adiciona pausas pra soar mais natural
        text_with_pauses = text.replace('.', '. ').replace(',', ', ')

        # Gera o áudio
        audio_file = io.BytesIO()
        temp_file = 'temp.wav'
        engine.save_to_file(text_with_pauses, temp_file)
        engine.runAndWait()

        # Lê o arquivo e converte pra base64
        with open(temp_file, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Remove o arquivo temporário
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return io.BytesIO(audio_data), audio_base64

    except Exception as e:
        logging.exception("Erro ao gerar áudio:")
        raise HTTPException(status_code=500, detail=f"Eita, algo deu errado: {str(e)}")

@app.post("/generate_audio/")
async def generate_audio_endpoint(
    text: str = Query(..., min_length=1), 
    lang: str = Query("pt-BR", max_length=5), 
    voice: str = Query("normal")
):
    """
    Recebe texto, idioma e voz, e devolve o áudio em base64.
    """
    audio_file, audio_base64 = generate_audio_data(text, lang, voice)
    return JSONResponse(content={"audio_base64": audio_base64})

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Página simples pra testar as vozes.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Gerador de Vozes Maneiras</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f0f0f0; }
        h1 { color: #34495e; }
        textarea { border-radius: 5px; padding: 10px; width: 100%; max-width: 500px; }
        select { padding: 8px; border-radius: 5px; }
        button { padding: 12px 25px; background-color: #e74c3c; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #c0392b; }
        label { font-weight: bold; margin-right: 10px; }
        .container { max-width: 600px; margin: 0 auto; }
    </style>
    <script>
        async function generateAudio() {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('langSelect').value;
            const voice = document.getElementById('voiceSelect').value;

            if (!text.trim()) {
                alert("Ei, coloca um texto pra eu falar, vai!");
                return;
            }

            try {
                const response = await fetch(`/generate_audio/?text=${encodeURIComponent(text)}&lang=${lang}&voice=${voice}`, {
                    method: 'POST',
                });

                if (response.ok) {
                    const data = await response.json();
                    const audio = new Audio('data:audio/wav;base64,' + data.audio_base64);
                    audio.play();
                    alert("Tá na mão! Ouviu direitinho?");
                } else {
                    alert("Ih, deu um probleminha... Vamos tentar de novo?");
                    console.error("Erro:", await response.text());
                }
            } catch (error) {
                alert("Ops, a internet deu uma vacilada. Tenta aí mais uma vez?");
                console.error("Erro na conexão:", error);
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>E aí, quer ouvir sua voz em outra vibe?</h1>
        <textarea id="textInput" placeholder="Escreve algo pra eu falar com estilo..." rows="5" cols="50"></textarea><br><br>
        <label for="langSelect">Qual idioma eu falo?</label>
        <select id="langSelect">
            <option value="pt-BR">Português (Brasil)</option>
            <option value="en-US">Inglês</option>
            <option value="es-ES">Espanhol</option>
        </select><br><br>
        <label for="voiceSelect">Que voz eu coloco?</label>
        <select id="voiceSelect">
            <option value="normal">Normal, bem tranquilo</option>
            <option value="man">Voz de homem, tipo narrador</option>
            <option value="woman">Voz de mulher, bem suave</option>
        </select><br><br>
        <button onclick="generateAudio()">Toca essa voz pra mim!</button>
    </div>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    print("Tá vindo aí! Só um segundinho que eu ligo o servidor pra você!")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
