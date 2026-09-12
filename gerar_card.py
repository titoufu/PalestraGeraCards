import base64
import os
import shutil
import subprocess
import sys
from datetime import datetime

import firebase_admin
import requests
from firebase_admin import credentials, db


def _pasta_recursos():
    """Onde ficam os arquivos só de leitura: logo, fontes, wkhtmltoimage.
    Quando empacotado (PyInstaller), isso fica numa pasta temporária interna."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _pasta_dados():
    """Onde ficam os arquivos que o usuário pode ver/trocar: a chave do
    Firebase e a pasta de cards gerados. Fica sempre ao lado do .exe (ou
    do script), nunca dentro da pasta temporária do empacotamento."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


PASTA_RECURSOS = _pasta_recursos()
PASTA_BASE = _pasta_dados()
PASTA_ASSETS = os.path.join(PASTA_RECURSOS, "assets")
PASTA_SAIDA = os.path.join(PASTA_BASE, "cards_gerados")

# Ordem de busca do wkhtmltoimage: primeiro o embutido junto com o programa,
# depois o PATH do sistema, depois o caminho padrão de instalação no Windows.
CAMINHO_WKHTMLTOIMAGE_EMBUTIDO = os.path.join(PASTA_RECURSOS, "wkhtmltoimage_bin", "wkhtmltoimage.exe")
CAMINHO_RESERVA_WKHTMLTOIMAGE = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe"

HORARIO_PADRAO = "19h30 às 20h30"
ENDERECO_PADRAO = "Rua Ângelo Cunha, 25 – São Jorge – Uberlândia"

DIAS_SEMANA = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA",
               "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]



def b64_arquivo(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def inicializar_firebase():
    caminho_chave = os.path.join(PASTA_BASE, "serviceAccountKey.json")
    cred = credentials.Certificate(caminho_chave)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://marialobato-v1-default-rtdb.firebaseio.com"
    })


def buscar_palestra(numero):
    dados = db.reference(f"palestra/{numero}").get()
    if not dados:
        raise ValueError(f"Nenhuma palestra encontrada para o número {numero}")
    return dados


def obter_foto_b64(foto_url):
    if not foto_url:
        return None
    resposta = requests.get(foto_url, timeout=15)
    resposta.raise_for_status()
    return base64.b64encode(resposta.content).decode("utf-8")


def dia_semana_extenso(data_str):
    data = datetime.strptime(data_str, "%d/%m/%Y")
    return DIAS_SEMANA[data.weekday()]


def montar_html(nome, tema, data_str, foto_b64):
    logo_b64 = b64_arquivo(os.path.join(PASTA_ASSETS, "logo.jpg"))
    fonte_bold_b64 = b64_arquivo(os.path.join(PASTA_ASSETS, "fonts", "PlayfairDisplay-Bold.woff"))
    fonte_regular_b64 = b64_arquivo(os.path.join(PASTA_ASSETS, "fonts", "PlayfairDisplay-Regular.woff"))

    dia_semana = dia_semana_extenso(data_str)

    if foto_b64:
        foto_html = f'<img class="foto" src="data:image/jpeg;base64,{foto_b64}">'
    else:
        foto_html = '''
        <div class="foto foto-silhueta">
            <svg viewBox="0 0 200 200" width="220" height="220">
                <circle cx="100" cy="100" r="100" fill="#c9d6e3"/>
                <circle cx="100" cy="78" r="34" fill="#8fa4b8"/>
                <path d="M40,175 C40,130 160,130 160,175 Z" fill="#8fa4b8"/>
            </svg>
        </div>
        '''

    html = f'''
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{ margin: 0; }}
        @font-face {{
            font-family: 'PlayfairTitulo';
            src: url(data:font/woff;base64,{fonte_bold_b64}) format('woff');
            font-weight: bold;
        }}
        @font-face {{
            font-family: 'PlayfairTitulo';
            src: url(data:font/woff;base64,{fonte_regular_b64}) format('woff');
            font-weight: normal;
        }}
        body {{
            margin: 0;
            width: 1080px;
            height: 1350px;
            font-family: 'DejaVu Sans', sans-serif;
            background-color: #6fa3d8;
            position: relative;
        }}
        .topo {{
            padding: 55px 70px 20px 90px;
            overflow: hidden;
        }}
        .logo {{
            float: left;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: white;
            object-fit: contain;
            padding: 6px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            margin-right: 40px;
        }}
        .instituicao {{
            overflow: hidden;
            padding-top: 26px;
            font-family: 'PlayfairTitulo', serif;
            color: #ffffff;
            font-size: 40px;
            font-weight: bold;
            text-align: left;
            text-shadow: 0 2px 6px rgba(0,0,0,0.35);
            line-height: 1.22;
        }}
        .rotulo-wrap {{
            text-align: center;
            margin-top: 22px;
        }}
        .rotulo-linha {{
            display: inline-block;
            vertical-align: middle;
            width: 90px;
            height: 2px;
            background: rgba(255,255,255,0.6);
        }}
        .rotulo {{
            display: inline-block;
            vertical-align: middle;
            color: #eaf6ff;
            font-size: 36px;
            letter-spacing: 8px;
            font-weight: bold;
            margin: 0 22px;
        }}
        .painel {{
            position: absolute;
            top: 340px;
            left: 60px;
            right: 60px;
            bottom: 60px;
            background: white;
            border-radius: 36px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            padding: 30px 60px 4px 60px;
            text-align: center;
            overflow: hidden;
        }}
        .foto {{
            width: 240px;
            height: 240px;
            border-radius: 50%;
            object-fit: cover;
            border: 8px solid #4a86c8;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        }}
        .foto-silhueta {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: #eef3f8;
        }}
        .nome {{
            margin-top: 20px;
            font-size: 38px;
            font-weight: bold;
            line-height: 1.15;
            color: #1f3a5f;
        }}
        .data-badge {{
            display: inline-block;
            margin-top: 18px;
            background: #26346b;
            color: white;
            border-radius: 20px;
            padding: 20px 40px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            text-align: left;
        }}
        .data-badge .linha-icone {{
            margin: 6px 0;
        }}
        .data-badge .linha-icone svg {{
            vertical-align: middle;
            margin-right: 14px;
        }}
        .data-badge .linha-icone span {{
            vertical-align: middle;
        }}
        .data-badge .dia-semana {{
            font-size: 20px;
            letter-spacing: 2px;
            opacity: 1;
            font-weight: bold;
            display: block;
        }}
        .data-badge .data-linha {{
            font-size: 28px;
            font-weight: bold;
        }}
        .data-badge .horario-linha {{
            font-size: 24px;
        }}
        .tema-box {{
            margin-top: 26px;
            background: #eaf3fb;
            border: 3px solid #a9cfe8;
            border-radius: 24px;
            padding: 34px 44px;
        }}
        .tema-rotulo {{
            font-size: 22px;
            font-weight: bold;
            color: #4a86c8;
            letter-spacing: 2px;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}
        .tema-texto {{
            font-family: 'PlayfairTitulo', serif;
            font-size: 40px;
            font-weight: bold;
            font-style: normal;
            color: #16233d;
            line-height: 1.3;
        }}
        .endereco {{
            margin-top: 20px;
            font-size: 24px;
            font-weight: 600;
            color: #2c3e55;
        }}
    </style>
    </head>
    <body>
        <div class="topo">
            <img class="logo" src="data:image/jpeg;base64,{logo_b64}">
            <div class="instituicao">Lar Espírita<br>Maria Lobato de Freitas</div>
        </div>
        <div class="rotulo-wrap">
            <span class="rotulo-linha"></span>
            <span class="rotulo">PALESTRA</span>
            <span class="rotulo-linha"></span>
        </div>

        <div class="painel">
            {foto_html}
            <div class="nome">{nome}</div>
            <div class="data-badge">
                <span class="dia-semana">{dia_semana}</span>
                <div class="linha-icone">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                        <rect x="3" y="5" width="18" height="16" rx="2" stroke="white" stroke-width="2"/>
                        <line x1="3" y1="10" x2="21" y2="10" stroke="white" stroke-width="2"/>
                        <line x1="7" y1="3" x2="7" y2="7" stroke="white" stroke-width="2"/>
                        <line x1="17" y1="3" x2="17" y2="7" stroke="white" stroke-width="2"/>
                    </svg>
                    <span class="data-linha">{data_str}</span>
                </div>
                <div class="linha-icone">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="9" stroke="white" stroke-width="2"/>
                        <line x1="12" y1="7" x2="12" y2="12" stroke="white" stroke-width="2"/>
                        <line x1="12" y1="12" x2="16" y2="14" stroke="white" stroke-width="2"/>
                    </svg>
                    <span class="horario-linha">{HORARIO_PADRAO}</span>
                </div>
            </div>
            <div class="tema-box">
                <div class="tema-rotulo">Tema:</div>
                <div class="tema-texto">"{tema}"</div>
            </div>
            <div class="endereco">{ENDERECO_PADRAO}</div>
        </div>
    </body>
    </html>
    '''
    return html


def localizar_wkhtmltoimage():
    if os.path.isfile(CAMINHO_WKHTMLTOIMAGE_EMBUTIDO):
        return CAMINHO_WKHTMLTOIMAGE_EMBUTIDO
    encontrado = shutil.which("wkhtmltoimage")
    if encontrado:
        return encontrado
    if os.path.isfile(CAMINHO_RESERVA_WKHTMLTOIMAGE):
        return CAMINHO_RESERVA_WKHTMLTOIMAGE
    raise FileNotFoundError(
        "Não encontrei o wkhtmltoimage. Confirme se a pasta wkhtmltoimage_bin "
        "está ao lado deste programa, com o wkhtmltoimage.exe dentro."
    )


def gerar_imagem(html_str, caminho_saida):
    caminho_html_temp = os.path.join(PASTA_BASE, "_tmp_card.html")
    with open(caminho_html_temp, "w", encoding="utf-8") as f:
        f.write(html_str)
    executavel = localizar_wkhtmltoimage()
    subprocess.run(
        [executavel, "--width", "1080", "--height", "1350",
         "--disable-smart-width", caminho_html_temp, caminho_saida],
        check=True
    )
    os.remove(caminho_html_temp)


def gerar_card(numero):
    palestra = buscar_palestra(numero)

    nome = palestra.get("orador", "").strip()
    tema = palestra.get("tema", "").strip()
    data_str = palestra.get("data", "")
    foto_url = palestra.get("fotoUrl")

    foto_b64 = obter_foto_b64(foto_url)
    html = montar_html(nome, tema, data_str, foto_b64)

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    dia, mes, ano = data_str.split("/")
    caminho_saida = os.path.join(PASTA_SAIDA, f"card_{dia}_{mes}_{ano}.png")
    gerar_imagem(html, caminho_saida)
    return caminho_saida


def gerar_card_por_data(data_str):
    """Recebe a data no formato DD/MM/AAAA e gera o card correspondente."""
    dia, mes, ano = data_str.split("/")
    numero = ano + mes + dia
    inicializar_firebase_se_preciso()
    return gerar_card(numero)


_firebase_iniciado = False


def inicializar_firebase_se_preciso():
    global _firebase_iniciado
    if not _firebase_iniciado:
        inicializar_firebase()
        _firebase_iniciado = True


def listar_cards_gerados():
    """Retorna a lista de caminhos dos cards já gerados, do mais recente pro mais antigo."""
    if not os.path.isdir(PASTA_SAIDA):
        return []
    arquivos = []
    for nome_arquivo in os.listdir(PASTA_SAIDA):
        if not nome_arquivo.startswith("card_") or not nome_arquivo.endswith(".png"):
            continue
        try:
            partes = nome_arquivo[len("card_"):-len(".png")].split("_")
            dia, mes, ano = int(partes[0]), int(partes[1]), int(partes[2])
            data_ordenacao = datetime(ano, mes, dia)
        except Exception:
            continue
        arquivos.append((data_ordenacao, os.path.join(PASTA_SAIDA, nome_arquivo)))
    arquivos.sort(key=lambda item: item[0], reverse=True)
    return [caminho for _, caminho in arquivos]


def excluir_card(caminho):
    if os.path.isfile(caminho):
        os.remove(caminho)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python gerar_card.py DD/MM/AAAA")
        sys.exit(1)

    data_arg = sys.argv[1]
    try:
        dia, mes, ano = data_arg.split("/")
        numero = ano + mes + dia
    except Exception:
        print("Data inválida. Use o formato DD/MM/AAAA, por exemplo: 10/09/2026")
        sys.exit(1)

    inicializar_firebase()
    caminho = gerar_card(numero)
    print(f"Card gerado em: {caminho}")
