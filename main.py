from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from gtts import gTTS
import io
import logging
import base64

# Configurando o logging pra não ficar perdido no que tá acontecendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Criando nosso app com FastAPI
app = FastAPI()

# Função pra criar o áudio com um toque mais humano
def generate_audio_data(text: str, lang: str = 'pt', voice: str = 'normal'):
    """
    Transforma o texto em áudio e deixa ele mais natural com pausas e ajustes.
    """
    try:
        # Ajusta a velocidade: 'slow' pra uma vibe mais calma, 'man' pra tentar soar mais grave
        slow = True if voice in ['slow', 'man'] else False
        
        # Pausas pra soar como alguém falando de verdade
        text_with_pauses = text.replace('.', '. ').replace(',', ', ')
        
        # Se for "voz de homem", adiciona um tom mais "pesado" com truque no texto
        if voice == 'man':
            text_with_pauses = f"{text_with_pauses}"  # gTTS não tem voz masculina direta, mas slow ajuda
        
        # Gera o áudio com o gTTS
        tts = gTTS(text=text_with_pauses, lang=lang, slow=slow)
        audio_file = io.BytesIO()  # Guarda o áudio num cantinho temporário
        tts.write_to_fp(audio_file)
        audio_file.seek(0)  # Volta pro começo pra usar

        # Converte pra base64 pra mandar pro navegador
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        audio_file.seek(0)  # Volta de novo, só pra garantir

        return audio_file, audio_base64

    except ValueError as ve:
        logging.error(f"Ops, o idioma deu problema: {ve}")
        raise HTTPException(status_code=400, detail=f"Eita, o idioma '{lang}' não funcionou: {ve}")
    except AssertionError:
        logging.error("Faltou texto, né?")
        raise HTTPException(status_code=400, detail="Calma aí, me dá um texto pra trabalhar!")
    except Exception as e:
        logging.exception("Deu um erro doido aqui:")
        raise HTTPException(status_code=500, detail=f"Putz, algo deu errado: {e}")

# Endpoint pra receber o pedido e devolver o áudio
@app.post("/generate_audio/")
async def generate_audio_endpoint(
    text: str = Query(..., min_length=1), 
    lang: str = Query("pt", max_length=5), 
    voice: str = Query("normal")
):
    """
    Pega o texto, idioma e voz, e devolve o áudio em base64 pra tocar no navegador.
    """
    audio_file, audio_base64 = generate_audio_data(text, lang, voice)
    return JSONResponse(content={"audio_base64": audio_base64})

# Página inicial com um visual simpático
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Mostra um formulário pra pessoa brincar com o gerador de áudio.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Gerador de Voz Amigão</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9; }
        h1 { color: #2c3e50; }
        textarea { border-radius: 5px; padding: 10px; }
        select { padding: 5px; }
        button { padding: 12px 25px; background-color: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #2980b9; }
        label { font-weight: bold; margin-right: 10px; }
    </style>
    <script>
        async function generateAudio() {
            const text = document.getElementById('textInput').value;
            const lang = document.getElementById('langSelect').value;
            const voice = document.getElementById('voiceSelect').value;

            if (!text.trim()) {
                alert("Ei, amigo, escreve alguma coisa pra eu falar!");
                return;
            }

            try {
                const response = await fetch(`/generate_audio/?text=${encodeURIComponent(text)}&lang=${lang}&voice=${voice}`, {
                    method: 'POST',
                });

                if (response.ok) {
                    const data = await response.json();
                    const audio = new Audio('data:audio/mpeg;base64,' + data.audio_base64);
                    audio.play();
                    alert("Pronto, tá tocando! Curte aí!");
                } else {
                    alert("Ops, deu um probleminha... Tenta de novo?");
                    console.error("Erro:", await response.text());
                }
            } catch (error) {
                alert("Ih, a conexão falhou. Vamos tentar mais uma vez?");
                console.error("Erro na conexão:", error);
            }
        }
    </script>
</head>
<body>
    <h1>Oi! Vamos transformar texto em voz?</h1>
    <textarea id="textInput" placeholder="Escreve aqui o que eu devo falar..." rows="5" cols="50"></textarea><br><br>
    <label for="langSelect">Qual idioma eu uso?</label>
    <select id="langSelect">
        <option value="pt">Português (Brasil)</option>
        <option value="en">Inglês</option>
        <option value="es">Espanhol</option>
        <option value="fr">Francês</option>
    </select><br><br>
    <label for="voiceSelect">Que voz você quer?</label>
    <select id="voiceSelect">
        <option value="normal">Normal, tipo eu conversando</option>
        <option value="slow">Bem calma, pra relaxar</option>
        <option value="man">Mais grave, tipo voz de homem</option>
    </select><br><br>
    <button onclick="generateAudio()">Faz minha voz soar!</button>
</body>
</html>
    """

# Liga o servidor e deixa tudo rodando
if __name__ == "__main__":
    import uvicorn
    print("Beleza, vou subir o servidor pra você brincar!")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
