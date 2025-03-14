from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from gtts import gTTS
import io
import os
import logging
import base64

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Função para gerar o áudio e retornar tanto o BytesIO quanto o base64
def generate_audio_data(text: str, lang: str = 'pt', voice: str = 'normal'):
    try:
        # Ajusta a velocidade da voz com base na escolha do usuário
        slow = True if voice == 'slow' else False
        
        # Adiciona pausas simples com base em pontuação para humanizar
        text_with_pauses = text.replace('.', '. ').replace(',', ', ')  # Espaços após pontos e vírgulas para pausas naturais
        
        # Cria um objeto gTTS
        tts = gTTS(text=text_with_pauses, lang=lang, slow=slow)
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)  # Volta para o início do arquivo

        # Codifica o áudio em base64
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_file.seek(0)  # Volta o ponteiro para o início

        return audio_file, audio_base64

    except ValueError as ve:
        logging.error(f"Erro de valor (idioma): {ve}")
        raise HTTPException(status_code=400, detail=f"Idioma inválido: {lang}. Detalhes: {ve}")
    except AssertionError as ae:
        logging.error(f"Erro de asserção (texto vazio): {ae}")
        raise HTTPException(status_code=400, detail=f"O texto não pode estar vazio. Detalhes: {ae}")
    except Exception as e:
        logging.exception("Erro inesperado durante a geração do áudio:")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o áudio. Detalhes: {e}")

@app.post("/generate_audio/")
async def generate_audio_endpoint(text: str = Query(..., min_length=1), lang: str = Query("pt", max_length=5), voice: str = Query("normal")):
    """
    Gera um áudio a partir do texto fornecido e retorna um JSON com o base64.

    Args:
        text: O texto.
        lang: O código do idioma.
        voice: A voz escolhida ('normal' ou 'slow').

    Returns:
        JSONResponse: Um JSON contendo o base64 do áudio.

    Raises:
        HTTPException: Em caso de erros.
    """
    audio_file, audio_base64 = generate_audio_data(text, lang, voice)

    # Retorna JSON com o base64
    return JSONResponse(content={"audio_base64": audio_base64})

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve a página HTML principal com opções de idioma e voz.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Gerador de Áudio</title>
    <script>
        async function generateAudio() {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('langSelect').value;
            const voice = document.getElementById('voiceSelect').value;

            if (!text.trim()) {
                alert("Por favor, insira algum texto.");
                return;
            }

            try {
                const response = await fetch(`/generate_audio/?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}&voice=${encodeURIComponent(voice)}`, {
                    method: 'POST',
                });

                if (response.ok) {
                    const data = await response.json(); // Pega o JSON da resposta
                    const audioBase64 = data.audio_base64;

                    // Cria um elemento audio e usa o base64 para reproduzir
                    const audioElement = new Audio();
                    audioElement.src = 'data:audio/mpeg;base64,' + audioBase64;
                    audioElement.play();

                } else {
                    const errorText = await response.text();
                    alert(`Erro na API: ${response.status} - ${errorText}`);
                    console.error("Erro na API:", response.status, errorText);
                }
            } catch (error) {
                alert("Erro ao gerar o áudio.");
                console.error("Erro ao conectar com a API:", error);
            }
        }
    </script>
</head>
<body>
    <h1>Gerador de Áudio</h1>
    <textarea id="textInput" placeholder="Digite o texto aqui" rows="4" cols="50"></textarea><br><br>
    <label for="langSelect">Idioma:</label>
    <select id="langSelect">
        <option value="pt">Português (Brasil)</option>
        <option value="en">Inglês</option>
        <option value="es">Espanhol</option>
        <option value="fr">Francês</option>
        <option value="de">Alemão</option>
        <option value="it">Italiano</option>
        <option value="ja">Japonês</option>
        <option value="ko">Coreano</option>
        <option value="ru">Russo</option>
        <option value="ar">Árabe</option>
    </select><br><br>
    <label for="voiceSelect">Voz:</label>
    <select id="voiceSelect">
        <option value="normal">Voz Normal</option>
        <option value="slow">Voz Lenta</option>
    </select><br><br>
    <button onclick="generateAudio()">Gerar Áudio</button>
</body>
</html>
    """

if __name__ == "__main__":
    import eel
    import uvicorn
    eel.init("web")  # 'web' é um nome de pasta comum, mas pode ser qualquer nome

    # Define uma rota estática para servir o eel.js
    @app.get("/eel.js")
    async def eel_js():
        try:
            with open(os.path.join(os.path.dirname(__file__), "web", "eel.js"), "r") as f:
                content = f.read()
            return HTMLResponse(content=content, media_type="application/javascript")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="eel.js não encontrado. Verifique a configuração do Eel e a pasta 'web'.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ler eel.js: {e}")

    # Inicia o servidor FastAPI e a interface Eel
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    eel.start('index.html', size=(600, 400))
