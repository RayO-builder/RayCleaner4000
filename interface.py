import asyncio
from pathlib import Path
import sys
import flet as ft

from limpador import OPCOES_LIMPEZA, executar_limpeza, is_admin


def main(page: ft.Page):
    page.title = "Raycleaner 5.0"
    page.theme_mode = ft.ThemeMode.DARK

    # Resolve recursos na pasta do script ou dentro do bundle do PyInstaller
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    caminho_logo = str(base_dir / "logo.png")
    caminho_icone_arq = base_dir / "icone.ico"
    caminho_icone = str(caminho_icone_arq) if caminho_icone_arq.exists() else caminho_logo
    page.window.icon = caminho_icone

    # Ajusta a janela ao tamanho do cartão e tenta remover a barra nativa/fundo extra
    page.window.frameless = True
    page.window.bgcolor = ft.Colors.TRANSPARENT
    page.bgcolor = ft.Colors.TRANSPARENT
    page.window.width = 540
    page.window.height = 795
    page.window.resizable = False
    page.window.center()

    em_adm = is_admin()

    # Controle de pulso vermelho suave para avisos de ADM
    alerta_adm_ativo = not em_adm
    textos_aviso_adm: list[ft.Text] = []
    status_em_alerta_adm = not em_adm

    checkboxes = [
        ft.Checkbox(
            label=nome,
            value=True,
            fill_color=ft.Colors.WHITE,
            check_color=ft.Colors.BLACK,
        )
        for nome in OPCOES_LIMPEZA
    ]

    texto_log_inicial = ft.Text(
        "[INFO] Pronto para iniciar a limpeza."
        if em_adm
        else "[AVISO] Abra o programa como Administrador para limpar pastas do sistema.",
        color=ft.Colors.GREY_300 if em_adm else ft.Colors.RED_300,
        font_family="Consolas",
        size=12,
        max_lines=3,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    if not em_adm:
        textos_aviso_adm.append(texto_log_inicial)

    log_lista = ft.ListView(
        controls=[texto_log_inicial],
        auto_scroll=True,
        spacing=4,
        expand=True,
    )

    status_rodape = ft.Text(
        "Aguardando início..."
        if em_adm
        else "É necessário abrir como Administrador para limpar pastas do sistema.",
        color=ft.Colors.GREY_400 if em_adm else ft.Colors.RED_300,
        font_family="Consolas",
        size=12,
    )

    async def _pulsar_aviso_adm():
        """Alterna suavemente entre dois tons de vermelho quando há aviso de ADM."""
        tons = [ft.Colors.RED_300, ft.Colors.RED_600]
        idx = 0
        while True:
            await asyncio.sleep(0.85)
            if not alerta_adm_ativo:
                continue
            idx = 1 - idx
            cor_atual = tons[idx]
            alterou = False
            for txt in list(textos_aviso_adm):
                if txt.color != cor_atual:
                    txt.color = cor_atual
                    alterou = True
            if status_em_alerta_adm and status_rodape.color != cor_atual:
                status_rodape.color = cor_atual
                alterou = True
            if alterou:
                try:
                    page.update()
                except Exception:
                    break

    async def adicionar_log(
        mensagem: str,
        cor: str = ft.Colors.WHITE,
        piscar_adm: bool = False,
    ):
        nonlocal alerta_adm_ativo
        txt = ft.Text(
            mensagem,
            color=cor,
            font_family="Consolas",
            size=12,
            max_lines=3,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        if piscar_adm:
            textos_aviso_adm.append(txt)
            alerta_adm_ativo = True

        log_lista.controls.append(txt)
        page.update()
        try:
            await log_lista.scroll_to(offset=-1, duration=120)
        except Exception:
            pass

    def marcar_todos(e):
        for cb in checkboxes:
            cb.value = True
        page.update()

    def desmarcar_todos(e):
        for cb in checkboxes:
            cb.value = False
        page.update()

    async def fechar_janela(e):
        await page.window.close()

    async def iniciar_limpeza(e):
        nonlocal alerta_adm_ativo, status_em_alerta_adm
        selecionados = [cb.label for cb in checkboxes if cb.value]
        log_lista.controls.clear()
        textos_aviso_adm.clear()
        alerta_adm_ativo = False
        status_em_alerta_adm = False

        if not selecionados:
            await adicionar_log("[AVISO] Nenhuma opção selecionada.", ft.Colors.AMBER_300)
            status_rodape.value = "Nenhuma opção selecionada."
            status_rodape.color = ft.Colors.AMBER_300
            page.update()
            return

        botao_limpar.disabled = True
        status_rodape.value = "Limpando..."
        status_rodape.color = ft.Colors.GREY_400
        page.update()

        total_bytes = 0
        teve_erro_adm = False
        try:
            for item in selecionados:
                await adicionar_log(f"[INFO] Limpando {item}...", ft.Colors.GREY_300)
                try:
                    bytes_item, detalhe, ok = await asyncio.to_thread(
                        executar_limpeza, item
                    )
                    total_bytes += bytes_item
                    mb_item = bytes_item / (1024 * 1024)
                    cor_ok = ft.Colors.WHITE if ok else ft.Colors.AMBER_300
                    prefixo = "[OK]" if ok else "[AVISO]"
                    await adicionar_log(
                        f"{prefixo} {detalhe} | {mb_item:.2f} MB", cor_ok
                    )
                except PermissionError as perm_err:
                    teve_erro_adm = True
                    await adicionar_log(
                        f"[AVISO] {perm_err}",
                        ft.Colors.RED_300,
                        piscar_adm=True,
                    )
                except Exception as exc:
                    await adicionar_log(
                        f"[ERRO] Falha em '{item}': {exc}", ft.Colors.RED_400
                    )

            total_mb = total_bytes / (1024 * 1024)
            if teve_erro_adm:
                await adicionar_log(
                    f"[AVISO] Limpeza parcial ({total_mb:.2f} MB). "
                    "Abra o programa como Administrador para limpar essas pastas.",
                    ft.Colors.RED_300,
                    piscar_adm=True,
                )
                status_rodape.value = (
                    f"Abra como Administrador para pastas do sistema. ({total_mb:.2f} MB)"
                )
                status_rodape.color = ft.Colors.RED_300
                status_em_alerta_adm = True
                alerta_adm_ativo = True
            else:
                await adicionar_log(
                    f"[SUCESSO] Limpeza concluída! Total liberado: {total_mb:.2f} MB.",
                    ft.Colors.GREEN_400,
                )
                status_rodape.value = (
                    f"Limpeza concluída com sucesso! Foram liberados {total_mb:.2f} MB."
                )
                status_rodape.color = ft.Colors.GREEN_400
        finally:
            botao_limpar.disabled = False
            page.update()

    borda_padrao = ft.Border.all(1.2, ft.Colors.WHITE)

    cabecalho = ft.WindowDragArea(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Image(
                            src=caminho_logo,
                            width=56,
                            height=56,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Raycleaner 5.0",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Limpeza suave e organizada • Dark Soft",
                                    size=11,
                                    color=ft.Colors.GREY_400,
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=12,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.WHITE,
                    on_click=fechar_janela,
                    tooltip="Fechar",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
    )

    caixa_opcoes = ft.Container(
        content=ft.Column(
            controls=[
                *checkboxes,
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Marcar todos",
                            on_click=marcar_todos,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                side=ft.BorderSide(1, ft.Colors.WHITE),
                            ),
                        ),
                        ft.OutlinedButton(
                            "Desmarcar todos",
                            on_click=desmarcar_todos,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                side=ft.BorderSide(1, ft.Colors.WHITE),
                            ),
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=8,
        ),
        border=borda_padrao,
        border_radius=16,
        padding=16,
        bgcolor=ft.Colors.BLACK,
    )

    botao_limpar = ft.Button(
        content=ft.Text(
            "Iniciar limpeza",
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD,
            size=14,
        ),
        bgcolor=ft.Colors.WHITE,
        width=float("inf"),
        height=44,
        on_click=iniciar_limpeza,
    )

    caixa_log = ft.Container(
        content=log_lista,
        width=float("inf"),
        height=152,
        border=borda_padrao,
        border_radius=14,
        padding=12,
        bgcolor=ft.Colors.BLACK,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    rodape_espacado = ft.Container(
        content=status_rodape,
        padding=ft.Padding.only(top=2, bottom=8),
    )

    cartao_principal = ft.Container(
        width=500,
        height=755,
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(1.5, ft.Colors.WHITE),
        border_radius=24,
        padding=22,
        content=ft.Column(
            controls=[
                cabecalho,
                ft.Container(height=1, bgcolor=ft.Colors.GREY_900),
                ft.Text(
                    "O que vamos limpar hoje?",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                caixa_opcoes,
                botao_limpar,
                ft.Container(height=2, bgcolor=ft.Colors.WHITE),
                caixa_log,
                rodape_espacado,
            ],
            spacing=13,
        ),
    )

    page.add(
        ft.Container(
            content=cartao_principal,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
    )

    page.run_task(_pulsar_aviso_adm)


if __name__ == "__main__":
    ft.run(main)