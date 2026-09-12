import io
import os
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk
from tkcalendar import DateEntry

import gerar_card

try:
    import win32clipboard
    COPIAR_DISPONIVEL = True
except ImportError:
    COPIAR_DISPONIVEL = False


class AppGeradorCards(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Cards de Palestras — Lar Maria Lobato")
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        largura_janela = min(560, largura_tela - 60)
        altura_janela = min(780, altura_tela - 100)
        self.geometry(f"{largura_janela}x{altura_janela}")
        self.resizable(True, True)

        self.caminho_selecionado = None
        self.imagem_preview_tk = None

        self._montar_secao_geracao()
        self._montar_secao_lista()
        self._montar_secao_preview()

        self.atualizar_lista()

    # ---------- Montagem da interface ----------

    def _montar_secao_geracao(self):
        quadro = ttk.LabelFrame(self, text="Gerar novo card")
        quadro.pack(fill="x", padx=12, pady=10)

        ttk.Label(quadro, text="Data da palestra:").pack(side="left", padx=(10, 6), pady=10)

        self.seletor_data = DateEntry(
            quadro, date_pattern="dd/mm/yyyy", width=12
        )
        self.seletor_data.pack(side="left", pady=10)

        self.botao_gerar = ttk.Button(quadro, text="Gerar Card", command=self.gerar_card_clicado)
        self.botao_gerar.pack(side="left", padx=12, pady=10)

        self.status_label = ttk.Label(self, text="", foreground="#a00")
        self.status_label.pack(fill="x", padx=14)

    def _montar_secao_lista(self):
        quadro = ttk.LabelFrame(self, text="Cards gerados (mais recente primeiro)")
        quadro.pack(fill="both", expand=False, padx=12, pady=10)

        self.lista = tk.Listbox(quadro, height=6)
        self.lista.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        self.lista.bind("<<ListboxSelect>>", self.selecionar_item)

        barra_rolagem = ttk.Scrollbar(quadro, orient="vertical", command=self.lista.yview)
        barra_rolagem.pack(side="left", fill="y", pady=10)
        self.lista.config(yscrollcommand=barra_rolagem.set)

        quadro_botoes = ttk.Frame(quadro)
        quadro_botoes.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Button(quadro_botoes, text="Excluir", command=self.excluir_clicado).pack(fill="x", pady=4)

        texto_copiar = "Copiar imagem" if COPIAR_DISPONIVEL else "Copiar (indisponível)"
        self.botao_copiar = ttk.Button(
            quadro_botoes, text=texto_copiar, command=self.copiar_clicado,
            state="normal" if COPIAR_DISPONIVEL else "disabled"
        )
        self.botao_copiar.pack(fill="x", pady=4)

    def _montar_secao_preview(self):
        quadro = ttk.LabelFrame(self, text="Prévia")
        quadro.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.preview_label = ttk.Label(quadro, text="Selecione um card na lista")
        self.preview_label.pack(expand=True)

    # ---------- Ações ----------

    def gerar_card_clicado(self):
        data_str = self.seletor_data.get()
        self.status_label.config(text="Gerando, aguarde...", foreground="#555")
        self.update_idletasks()
        try:
            gerar_card.gerar_card_por_data(data_str)
            self.status_label.config(text="Card gerado com sucesso.", foreground="#070")
            self.atualizar_lista()
        except ValueError:
            self.status_label.config(
                text="Nenhuma palestra encontrada para essa data.", foreground="#a00"
            )
        except Exception as erro:
            self.status_label.config(text=f"Erro ao gerar: {erro}", foreground="#a00")

    def atualizar_lista(self):
        self.lista.delete(0, tk.END)
        self.caminhos_atuais = gerar_card.listar_cards_gerados()
        for caminho in self.caminhos_atuais:
            self.lista.insert(tk.END, os.path.basename(caminho))
        self.caminho_selecionado = None
        self.mostrar_preview(None)

    def selecionar_item(self, evento):
        selecao = self.lista.curselection()
        if not selecao:
            return
        indice = selecao[0]
        self.caminho_selecionado = self.caminhos_atuais[indice]
        self.mostrar_preview(self.caminho_selecionado)

    def mostrar_preview(self, caminho):
        if not caminho:
            self.preview_label.config(image="", text="Selecione um card na lista")
            self.imagem_preview_tk = None
            return
        imagem = Image.open(caminho)
        imagem.thumbnail((288, 360))
        self.imagem_preview_tk = ImageTk.PhotoImage(imagem)
        self.preview_label.config(image=self.imagem_preview_tk, text="")

    def excluir_clicado(self):
        if not self.caminho_selecionado:
            messagebox.showinfo("Excluir", "Selecione um card na lista primeiro.")
            return
        nome_arquivo = os.path.basename(self.caminho_selecionado)
        confirmar = messagebox.askyesno("Excluir card", f"Excluir o arquivo {nome_arquivo}?")
        if confirmar:
            gerar_card.excluir_card(self.caminho_selecionado)
            self.atualizar_lista()

    def copiar_clicado(self):
        if not self.caminho_selecionado:
            messagebox.showinfo("Copiar", "Selecione um card na lista primeiro.")
            return
        try:
            self._copiar_imagem_para_clipboard(self.caminho_selecionado)
            self.status_label.config(text="Imagem copiada — cole com Ctrl+V no WhatsApp.", foreground="#070")
        except Exception as erro:
            self.status_label.config(text=f"Erro ao copiar: {erro}", foreground="#a00")

    @staticmethod
    def _copiar_imagem_para_clipboard(caminho_imagem):
        imagem = Image.open(caminho_imagem).convert("RGB")
        saida = io.BytesIO()
        imagem.save(saida, "BMP")
        dados = saida.getvalue()[14:]  # remove o cabeçalho de arquivo BMP, mantém só o DIB
        saida.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dados)
        win32clipboard.CloseClipboard()


if __name__ == "__main__":
    app = AppGeradorCards()
    app.mainloop()
