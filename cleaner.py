import sys
import os
import shutil
import subprocess
import tempfile
import ctypes
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PASTA_BASE = Path(__file__).resolve().parent


def verificar_admin() -> bool:
    """Verifica se o programa está rodando com privilégios de Administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def obter_tamanho_pasta(caminho: Path) -> int:
    total = 0
    if not caminho.exists():
        return 0
    for raiz, _, arquivos in os.walk(caminho):
        for nome in arquivos:
            try:
                total += (Path(raiz) / nome).stat().st_size
            except OSError:
                pass
    return total


def formatar_bytes(tamanho: int) -> str:
    if tamanho < 1024:
        return f"{tamanho} B"
    if tamanho < 1024**2:
        return f"{tamanho / 1024:.1f} KB"
    if tamanho < 1024**3:
        return f"{tamanho / (1024**2):.1f} MB"
    return f"{tamanho / (1024**3):.2f} GB"


def limpar_conteudo_pasta(caminho: Path) -> int:
    if not caminho or not caminho.exists():
        return 0

    liberado = 0
    for item in caminho.iterdir():
        try:
            if item.is_symlink() or item.is_file():
                try:
                    tamanho = item.stat().st_size
                except OSError:
                    tamanho = 0
                item.unlink()
                liberado += tamanho
            elif item.is_dir():
                tamanho_antes = obter_tamanho_pasta(item)
                shutil.rmtree(item, ignore_errors=True)
                tamanho_depois = obter_tamanho_pasta(item)
                liberado += max(0, tamanho_antes - tamanho_depois)
        except OSError:
            pass
    return liberado


def obter_caminho_recurso(nome_arquivo: str) -> Path:
    """Retorna o caminho correto do arquivo, seja em desenvolvimento ou empacotado pelo PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / nome_arquivo
    return PASTA_BASE / nome_arquivo


def carregar_imagens_logo() -> tuple[ctk.CTkImage | None, Image.Image | None]:
    for nome_arquivo in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.ico"):
        caminho_logo = obter_caminho_recurso(nome_arquivo)
        if caminho_logo.exists():
            try:
                img = Image.open(caminho_logo).convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(112, 112))
                return ctk_img, img
            except Exception:
                return None, None
    return None, None


class Raycleaner4000App(ctk.CTk):
    _ESTADOS_BOTAO = [
        ("Limpando.", "#7AA2F7", "#0F172A"),
        ("Limpando..", "#6EE7B7", "#0F2419"),
        ("Limpando...", "#93C5FD", "#0F172A"),
    ]

    def __init__(self):
        super().__init__()

        self.title("Raycleaner4000")
        self.geometry("960x820")
        self.minsize(820, 720)
        self.resizable(True, True)
        self.configure(fg_color="#12151C")

        temp_env = os.environ.get("TEMP")
        appdata_env = os.environ.get("APPDATA")

        self.opcoes_vars = {}
        self.opcoes_info = [
            ("win_temp", "Arquivos do sistema (C:\\Windows\\Temp)", Path(r"C:\Windows\Temp")),
            ("user_temp", "Temporários do usuário (%TEMP%)", Path(temp_env) if temp_env else None),
            ("prefetch", "Arquivos de Prefetch (C:\\Windows\\Prefetch)", Path(r"C:\Windows\Prefetch")),
            (
                "recent",
                "Arquivos recentes do Windows",
                Path(appdata_env) / r"Microsoft\Windows\Recent" if appdata_env else None,
            ),
            ("recycle_bin", "Esvaziar Lixeira", None),
        ]

        self.logo_ctk, self._logo_pil = carregar_imagens_logo()
        self._logo_tk_icon = None
        self._ico_temp_path = None
        self._limpando = False
        self._anim_job = None
        self._anim_passo = 0

        self._montar_interface()
        self.after(50, lambda: self.status_box.see("1.0"))
        self.after(150, self._aplicar_icone_janela)
        self.after(500, self._aplicar_icone_janela)

    def _aplicar_icone_janela(self):
        if self._logo_pil is None:
            return
        try:
            icone_quadrado = self._logo_pil.resize((64, 64), Image.Resampling.LANCZOS)
            self._logo_tk_icon = ImageTk.PhotoImage(icone_quadrado)
            self.wm_iconphoto(False, self._logo_tk_icon)

            ico_file = Path(tempfile.gettempdir()) / "raycleaner4000_icon.ico"
            icone_quadrado.save(
                ico_file,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
            )
            self._ico_temp_path = str(ico_file)
            self.iconbitmap(default=self._ico_temp_path)
            self.iconbitmap(self._ico_temp_path)
        except Exception:
            pass

    def _montar_interface(self):
        header = ctk.CTkFrame(
            self,
            fg_color="#181D27",
            height=148,
            corner_radius=16,
            border_width=1,
            border_color="#262E3D",
        )
        header.pack(fill="x", padx=22, pady=(22, 12))
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=20, pady=12)
        header_inner.grid_columnconfigure(0, minsize=120)
        header_inner.grid_columnconfigure(1, weight=1)
        header_inner.grid_columnconfigure(2, minsize=120)
        header_inner.grid_rowconfigure(0, weight=1)

        if self.logo_ctk is not None:
            lbl_logo = ctk.CTkLabel(
                header_inner,
                text="",
                image=self.logo_ctk,
                width=112,
                height=112,
            )
            lbl_logo.grid(row=0, column=0, sticky="w")
        else:
            badge = ctk.CTkFrame(
                header_inner,
                width=112,
                height=112,
                corner_radius=16,
                fg_color="#232B3B",
            )
            badge.grid(row=0, column=0, sticky="w")
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge,
                text="✦",
                font=ctk.CTkFont(size=36),
                text_color="#93C5FD",
            ).place(relx=0.5, rely=0.5, anchor="center")

        centro_titulo = ctk.CTkFrame(header_inner, fg_color="transparent")
        centro_titulo.grid(row=0, column=1)

        ctk.CTkLabel(
            centro_titulo,
            text="Raycleaner4000",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#F1F5F9",
        ).pack()

        ctk.CTkLabel(
            centro_titulo,
            text="Limpeza suave e organizada • Dark Soft",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8",
        ).pack(pady=(4, 0))

        card_opcoes = ctk.CTkFrame(
            self,
            fg_color="#181D27",
            corner_radius=16,
            border_width=1,
            border_color="#262E3D",
        )
        card_opcoes.pack(fill="x", padx=22, pady=6)

        ctk.CTkLabel(
            card_opcoes,
            text="O que vamos limpar hoje?",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E2E8F0",
        ).pack(anchor="w", padx=20, pady=(16, 8))

        for chave, texto, _ in self.opcoes_info:
            var = ctk.BooleanVar(value=True)
            self.opcoes_vars[chave] = var
            chk = ctk.CTkCheckBox(
                card_opcoes,
                text=texto,
                variable=var,
                font=ctk.CTkFont(size=14),
                text_color="#CBD5E1",
                fg_color="#7AA2F7",
                hover_color="#658CE0",
                border_color="#3B465B",
                corner_radius=6,
            )
            chk.pack(anchor="w", padx=22, pady=7)

        botoes_extra = ctk.CTkFrame(card_opcoes, fg_color="transparent")
        botoes_extra.pack(fill="x", padx=20, pady=(10, 16))

        ctk.CTkButton(
            botoes_extra,
            text="Marcar todos",
            width=135,
            height=34,
            corner_radius=10,
            fg_color="#232A38",
            hover_color="#2D3748",
            text_color="#CBD5E1",
            command=self._marcar_todos,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            botoes_extra,
            text="Desmarcar todos",
            width=145,
            height=34,
            corner_radius=10,
            fg_color="#232A38",
            hover_color="#2D3748",
            text_color="#CBD5E1",
            command=self._desmarcar_todos,
        ).pack(side="left")

        self.btn_limpar = ctk.CTkButton(
            self,
            text="Iniciar limpeza",
            height=48,
            corner_radius=13,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#86EFAC",
            hover_color="#6EE7B7",
            text_color="#0F2419",
            command=self._iniciar_limpeza,
        )
        self.btn_limpar.pack(fill="x", padx=22, pady=(14, 10))

        self.barra_progresso = ctk.CTkProgressBar(
            self,
            height=9,
            corner_radius=8,
            fg_color="#222938",
            progress_color="#7AA2F7",
        )
        self.barra_progresso.pack(fill="x", padx=22, pady=(0, 12))
        self.barra_progresso.set(0)

        self.status_box = ctk.CTkTextbox(
            self,
            height=170,
            fg_color="#161A22",
            text_color="#B8C4D4",
            border_width=1,
            border_color="#242C3A",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=14,
            wrap="word",
        )
        self.status_box.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        self.status_box.tag_config("normal", foreground="#B8C4D4")
        self.status_box.tag_config("sucesso", foreground="#86EFAC")
        self.status_box.tag_config("erro", foreground="#F87171")

        self._log("Tudo pronto por aqui. Escolha as opções e clique em Iniciar limpeza.", tipo="normal")

    def _log(self, mensagem: str, tipo: str = "normal"):
        self.status_box.insert("end", mensagem + "\n", tipo)
        self.status_box.see("end")

    def _iniciar_animacao_botao(self):
        self._limpando = True
        self._anim_passo = 0
        self.btn_limpar.configure(state="disabled")
        self._ciclo_animacao_botao()

    def _ciclo_animacao_botao(self):
        if not self._limpando:
            return
        texto, cor_fundo, cor_texto = self._ESTADOS_BOTAO[self._anim_passo % len(self._ESTADOS_BOTAO)]
        self.btn_limpar.configure(text=texto, fg_color=cor_fundo, text_color=cor_texto)
        self._anim_passo += 1
        self._anim_job = self.after(280, self._ciclo_animacao_botao)

    def _parar_animacao_botao(self):
        self._limpando = False
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self.btn_limpar.configure(
            state="normal",
            text="Iniciar limpeza",
            fg_color="#86EFAC",
            hover_color="#6EE7B7",
            text_color="#0F2419",
        )

    def _marcar_todos(self):
        for var in self.opcoes_vars.values():
            var.set(True)

    def _desmarcar_todos(self):
        for var in self.opcoes_vars.values():
            var.set(False)

    def _iniciar_limpeza(self):
        # Validação de Permissão de Administrador
        if not verificar_admin():
            self.status_box.delete("1.0", "end")
            self._log("=== Erro de Permissão ===", tipo="erro")
            self._log("[x] O programa precisa de privilégios de Administrador para limpar o sistema.", tipo="erro")
            self._log("    Feche o programa e execute-o como Administrador.", tipo="erro")
            
            self.btn_limpar.configure(
                state="disabled",
                text="Erro: Sem Permissão de Admin",
                fg_color="#F87171",
                text_color="#450A0A"
            )
            self.after(3500, lambda: self.btn_limpar.configure(
                state="normal",
                text="Iniciar limpeza",
                fg_color="#86EFAC",
                hover_color="#6EE7B7",
                text_color="#0F2419"
            ))
            return

        selecionadas = [item for item in self.opcoes_info if self.opcoes_vars[item[0]].get()]
        if not selecionadas:
            self._log("[!] Nenhuma opção selecionada.", tipo="erro")
            return

        self._iniciar_animacao_botao()
        self.barra_progresso.set(0)
        self.status_box.delete("1.0", "end")
        self._log("=== Raycleaner4000 ===", tipo="normal")
        self.after(100, lambda: self._executar_etapas(selecionadas, 0, 0))

    def _executar_etapas(self, selecionadas, indice, total_liberado):
        if indice >= len(selecionadas):
            self.barra_progresso.set(1)
            self._log("----------------------------------------", tipo="normal")
            self._log(
                f"Concluído! Espaço liberado: {formatar_bytes(total_liberado)} — nice!",
                tipo="sucesso",
            )
            self._parar_animacao_botao()
            return

        chave, nome, caminho = selecionadas[indice]
        self._log(f"Limpando: {nome}...", tipo="normal")

        if chave == "recycle_bin":
            try:
                resultado = subprocess.run(
                    ["PowerShell", "-NoLogo", "-Command", "Clear-RecycleBin -Force"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if resultado.returncode == 0:
                    self._log("  -> Lixeira esvaziada.", tipo="normal")
                else:
                    self._log("  -> Lixeira já vazia ou sem itens removíveis.", tipo="normal")
            except Exception as e:
                self._log(f"  -> Erro na lixeira: {e}", tipo="erro")
        else:
            liberado_etapa = limpar_conteudo_pasta(caminho)
            total_liberado += liberado_etapa
            self._log(f"  -> Liberado: {formatar_bytes(liberado_etapa)}", tipo="normal")

        progresso = (indice + 1) / len(selecionadas)
        self.barra_progresso.set(progresso)
        self.after(150, lambda: self._executar_etapas(selecionadas, indice + 1, total_liberado))


if __name__ == "__main__":
    app = Raycleaner4000App()
    app.mainloop()