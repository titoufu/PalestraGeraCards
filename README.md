# Gerador de Cards de Palestras — Lar Espírita Maria Lobato de Freitas

Programa em Python com interface gráfica que lê as palestras cadastradas no
Firebase (mesmo banco usado pelos apps Android de cadastro e divulgação) e
gera um card visual (1080×1350) pronto pra divulgar no WhatsApp — com foto do
palestrante, data, horário e tema.

## Como o projeto se encaixa no todo

- **App Android "cadastro"** (`AppPalestraLanca`) — onde as palestras e o
  acervo de palestrantes (nome + foto) são lançados no Firebase.
- **App Android "listagem"** (`MALOB_AppPalestrasLista`) — mostra a agenda
  da semana/mês pros palestrantes.
- **Este projeto** — gera, a partir dos mesmos dados, uma imagem de
  divulgação por palestra.

Os três compartilham o mesmo projeto Firebase (`marialobato-v1`), Realtime
Database, nó `palestra` (uma palestra por data, chave `numero` no formato
`aaaammdd`) e nó `palestrante` (acervo reutilizável de nome + foto).

## Estrutura de pastas

```
GeradorCardPalestras/
├── gerar_card.py           # lógica de geração do card (template HTML + wkhtmltoimage)
├── gerador_gui.py          # interface gráfica (tkinter)
├── serviceAccountKey.json  # chave do Firebase Admin SDK — NUNCA vai pro Git
├── assets/
│   ├── logo.jpg
│   └── fonts/
│       ├── PlayfairDisplay-Bold.woff
│       └── PlayfairDisplay-Regular.woff
├── wkhtmltoimage_bin/      # cópia da pasta bin do wkhtmltopdf instalado — NÃO vai pro Git
├── cards_gerados/          # saída (criada automaticamente) — NÃO vai pro Git
└── venv/                   # ambiente virtual Python — NÃO vai pro Git
```

## Preparando o ambiente (desenvolvimento)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install firebase-admin requests Pillow tkcalendar pywin32 pyinstaller
```

Também é preciso, manualmente (não vem pelo pip):

1. **`serviceAccountKey.json`** — gerado em
   Console do Firebase → Configurações do projeto → Contas de serviço →
   Gerar nova chave privada. Colocar na raiz do projeto.
2. **`assets/logo.jpg`** — logo do Lar.
3. **`assets/fonts/`** — as duas fontes Playfair Display (Bold e Regular),
   formato `.woff`.
4. **`wkhtmltoimage_bin/`** — copiar o conteúdo de
   `C:\Program Files\wkhtmltopdf\bin` (depois de instalar o wkhtmltopdf a
   partir de https://github.com/wkhtmltopdf/packaging/releases) pra dentro
   dessa pasta.

## Rodando

Interface gráfica:
```bash
python gerador_gui.py
```

Linha de comando (gera um card específico, sem interface):
```bash
python gerar_card.py 10/09/2026
```

## Gerando o executável standalone (distribuição)

```bash
pyinstaller --onedir --windowed --name "GeradorDeCards" ^
  --add-data "assets;assets" ^
  --add-data "wkhtmltoimage_bin;wkhtmltoimage_bin" ^
  gerador_gui.py
```

Isso cria `dist\GeradorDeCards\`. Antes de distribuir:
- Copiar `serviceAccountKey.json` pra dentro dessa pasta (fica ao lado do
  `.exe`, fora do pacote em si — assim dá pra trocar a chave sem gerar tudo
  de novo).
- Compactar a pasta inteira em `.zip` e distribuir (extrair tudo antes de
  usar; o Windows vai avisar "protegeu seu PC" na primeira execução —
  normal, clicar em "Mais informações → Executar assim mesmo").

**Atenção de segurança:** quem recebe o pacote tem, em tese, acesso total ao
Firebase (a chave embutida dá acesso de administrador). Distribuir só pra
pessoas de confiança.

## Decisões técnicas / pegadinhas já resolvidas

- **O card é montado como HTML/CSS e renderizado com `wkhtmltoimage`**
  (motor WebKit antigo). Isso impõe limitações importantes de compatibilidade,
  especialmente entre o ambiente de desenvolvimento e a instalação oficial do
  Windows:
  - **Nunca usar `display: flex`** — o build oficial do Windows ignora essa
    propriedade (elementos viram `block`/`inline` normais, quebrando o
    layout). Usar `float`, `inline-block` + `text-align`, ou posicionamento
    absoluto no lugar.
  - **Nunca usar `gap` no flexbox** — não é aplicado; usar `margin`.
  - **Nunca usar `linear-gradient()`** — não renderiza; usar cor sólida
    (`background-color`).
  - **Sempre passar `--disable-smart-width`** pro `wkhtmltoimage`, senão ele
    encolhe a página pro tamanho "ideal" do conteúdo em vez de respeitar
    `--width`/`--height`.
- **O painel branco usa `position: absolute` com `top`/`left`/`right`/`bottom`
  fixos** (em vez de margem + altura automática) — isso garante que a margem
  azul embaixo seja sempre igual à dos lados, não importa se o nome do
  palestrante ou o tema ocupam uma ou várias linhas. `overflow: hidden` no
  painel evita que um texto excepcionalmente longo vaze pra fora dele.
- **Card sem foto do palestrante:** usa uma silhueta genérica desenhada em
  SVG embutido (sem depender de arquivo externo).

## Referência de dados no Firebase

Nó `palestra/{numero}`:
| Campo | Formato | Observação |
|---|---|---|
| `data` | `dd/mm/aaaa` | |
| `orador` | texto livre | |
| `tema` | texto livre | |
| `referencia` | texto livre | não aparece no card |
| `numero` | `aaaammdd` | chave de ordenação/busca |
| `fotoUrl` | URL do Firebase Storage | opcional |

Nó `palestrante/{id}`: `nome`, `fotoUrl` (acervo reutilizável, usado pela
busca no campo Orador do app de cadastro).
