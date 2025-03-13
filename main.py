from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from gtts import gTTS
import io  
import os  # Importe o módulo 'os'
import logging  # Importe o módulo 'logging'


# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Função para gerar o áudio, agora com tratamento de erros aprimorado e escolha de idioma
def generate_audio_file(text: str, lang: str = 'pt') -> io.BytesIO:
    try:
        # Cria um objeto gTTS.  Lida com exceções específicas.
        tts = gTTS(text=text, lang=lang, slow=False)  # slow=False é o padrão, mas é bom explicitar
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)  # Volta para o início do arquivo
        return audio_file
    except ValueError as ve:  # Idioma inválido
        logging.error(f"Erro de valor (idioma): {ve}")  # Loga o erro
        raise HTTPException(status_code=400, detail=f"Idioma inválido: {lang}.  Use um código de idioma válido (ex: 'pt', 'en', 'es').  Detalhes: {ve}")
    except AssertionError as ae: #Erro se o texto estiver vazio
        logging.error(f"Erro de asserção (texto vazio): {ae}")
        raise HTTPException(status_code=400, detail= f"O texto não pode estar vazio. Detalhes:{ae}")
    except Exception as e:  # Captura QUALQUER outra exceção
        logging.exception("Erro inesperado durante a geração do áudio:")  # Loga a exceção COMPLETA com traceback
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o áudio.  Detalhes: {e}")


@app.post("/generate_audio/")
async def generate_audio_endpoint(text: str = Query(..., min_length=1), lang: str = Query("pt", max_length=5)): #Query valida e da mais informações sobre possiveis erros.
    """
    Gera um áudio a partir do texto fornecido.

    Args:
        text: O texto a ser convertido em áudio (obrigatório, mínimo 1 caractere).
        lang: O código do idioma (opcional, padrão 'pt', máximo 5 caracteres).

    Returns:
        StreamingResponse: Um stream do áudio em formato MP3.

    Raises:
        HTTPException: Erros relacionados à validação ou geração do áudio.
    """
    audio_file = generate_audio_file(text, lang)
    return StreamingResponse(audio_file, media_type="audio/mpeg")



@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve a página HTML principal para interação com a API.
    """
    #  Um HTML *inline* simples para testar.  Em um projeto real,
    #  você usaria templates (Jinja2, por exemplo) para organizar melhor o HTML.
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gerador de Áudio</title>
        <script type="text/javascript" src="/eel.js"></script>
        <script>
             async function generateAudio() {
                const text = document.getElementById('textInput').value;
                const lang = document.getElementById('langSelect').value;

                //Validação básica no frontend (opcional mas recomendado)
                if (!text.trim()){
                    alert("Por favor, insira algum texto.");
                    return;
                }


                try {
                    const response = await fetch(`/generate_audio/?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}`, {
                        method: 'POST', //Usando POST como na definição da API
                    });


                    if (response.ok) { //Verifica se a resposta foi bem sucedida
                        const blob = await response.blob();
                        const audioUrl = URL.createObjectURL(blob);
                        const audioElement = new Audio(audioUrl);
                        audioElement.play();
                    } else {
                        //Trata erros da API (ex: 400, 500)
                        const errorText = await response.text(); //Pega o texto do erro.
                        alert(`Erro na API: ${response.status} - ${errorText}`); //Exibe o erro
                        console.error("Erro na API:", response.status, errorText);

                    }
                } catch (error) {
                    //Trata erros de rede, fetch, etc.
                    alert("Erro ao gerar o áudio. Verifique o console para detalhes.");
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
            <!-- Adicione mais idiomas conforme necessário -->
        </select><br><br>
        <button onclick="generateAudio()">Gerar Áudio</button>

    </body>
    </html>
    """

# Inicialização do Eel (apenas se este arquivo for executado diretamente)
if __name__ == "__main__":
    import eel
    eel.init("web")  # 'web' é um nome de pasta comum, mas pode ser qualquer nome

    # Define uma rota estática para servir o eel.js
    # Isso corrige o erro 404 para /eel.js.  É *fundamental*.
    @app.get("/eel.js")
    async def eel_js():
        # Lê o conteúdo do arquivo eel.js (caminho relativo!)
        try:
            with open(os.path.join(os.path.dirname(__file__), "web", "eel.js"), "r") as f:
                content = f.read()
            return HTMLResponse(content=content, media_type="application/javascript")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="eel.js não encontrado. Verifique a configuração do Eel e a pasta 'web'.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ler eel.js: {e}")
            

    # Inicia o servidor FastAPI (usando uvicorn, recomendado para produção)
    # e, logo em seguida, a interface Eel.
    # A ordem *importa*: FastAPI primeiro, depois Eel.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")  # Use log_level="debug" para mais detalhes durante o desenvolvimento
    eel.start('index.html', size=(600, 400))  # Ajuste o tamanho da janela conforme necessário
