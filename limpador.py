import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil

# Constantes da API do Windows para esvaziar a Lixeira sem diálogos pop-up
SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004

OPCOES_LIMPEZA = [
    "Arquivos do sistema (C:\\Windows\\Temp)",
    "Temporários do usuário (%TEMP%)",
    "Arquivos de Prefetch (C:\\Windows\\Prefetch)",
    "Arquivos recentes do Windows",
    "Esvaziar Lixeira",
]


def is_admin() -> bool:
    """Verifica se o processo atual está rodando com privilégios de Administrador."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _tamanho_arquivo_seguro(caminho: Path) -> int:
    try:
        if caminho.is_symlink():
            return 0
        return caminho.stat().st_size
    except OSError:
        return 0


def _calcular_tamanho_pasta(pasta: Path) -> tuple[int, int]:
    """Retorna (total_bytes, total_arquivos) dentro de `pasta` sem apagar nada."""
    if not pasta.exists() or not pasta.is_dir():
        return (0, 0)

    total_bytes = 0
    total_arquivos = 0
    for root, _, files in os.walk(pasta):
        for nome in files:
            arq = Path(root) / nome
            total_bytes += _tamanho_arquivo_seguro(arq)
            total_arquivos += 1
    return (total_bytes, total_arquivos)


def _limpar_pasta_conteudo(pasta: Path) -> tuple[int, int, int]:
    """Apaga arquivos e subpastas dentro de `pasta` e soma o tamanho real removido.

    Retorna: (bytes_liberados, itens_removidos, itens_ignorados)
    """
    if not pasta.exists() or not pasta.is_dir():
        return (0, 0, 0)

    bytes_liberados = 0
    removidos = 0
    ignorados = 0

    for entrada in pasta.iterdir():
        try:
            if entrada.is_symlink() or entrada.is_file():
                tamanho = _tamanho_arquivo_seguro(entrada)
                entrada.unlink(missing_ok=False)
                bytes_liberados += tamanho
                removidos += 1
            elif entrada.is_dir():
                tamanho_antes, _ = _calcular_tamanho_pasta(entrada)
                shutil.rmtree(entrada, ignore_errors=False)
                tamanho_depois, _ = _calcular_tamanho_pasta(entrada)
                bytes_liberados += max(0, tamanho_antes - tamanho_depois)
                removidos += 1
        except (PermissionError, OSError):
            ignorados += 1

    return (bytes_liberados, removidos, ignorados)


def _calcular_tamanho_lixeira() -> tuple[int, int]:
    """Mede os itens atuais na Lixeira em todas as unidades via SHQueryRecycleBinW e fallback."""

    class SHQUERYRBINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("i64Size", ctypes.c_longlong),
            ("i64NumItems", ctypes.c_longlong),
        ]

    total_bytes = 0
    total_itens = 0

    try:
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        hr = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
        if hr == 0 and info.i64Size >= 0:
            total_bytes = int(info.i64Size)
            total_itens = int(info.i64NumItems)
    except Exception:
        pass

    if total_bytes == 0:
        for letra in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            recycle_root = Path(f"{letra}:\\$Recycle.Bin")
            if not recycle_root.exists():
                continue
            try:
                for entrada in recycle_root.rglob("*"):
                    try:
                        if entrada.is_file() and not entrada.name.startswith("$I"):
                            total_bytes += _tamanho_arquivo_seguro(entrada)
                            total_itens += 1
                    except OSError:
                        continue
            except OSError:
                continue

    return (total_bytes, total_itens)


def _esvaziar_lixeira_windows() -> tuple[int, bool, str]:
    """Mede a Lixeira, esvazia via API do Windows e retorna bytes liberados."""
    bytes_antes, qtd_antes = _calcular_tamanho_lixeira()
    try:
        shell32 = ctypes.windll.shell32
        resultado = shell32.SHEmptyRecycleBinW(
            None,
            None,
            SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND,
        )
        # S_OK (0) = esvaziada; S_FALSE (-2147418113 / 0x8000FFFF) = já estava vazia
        if resultado == 0:
            return (
                max(0, bytes_antes),
                True,
                f"Lixeira esvaziada ({qtd_antes} item(ns) detectado(s))",
            )
        if resultado == -2147418113:
            return (0, True, "Lixeira já estava vazia")
        return (0, False, f"Lixeira retornou código {resultado}")
    except Exception as exc:
        return (0, False, f"Erro ao esvaziar Lixeira: {exc}")


def executar_limpeza(opcao: str) -> tuple[int, str, bool]:
    """Executa uma opção de limpeza e retorna (bytes_liberados, mensagem_status, ok)."""
    if opcao == "Arquivos do sistema (C:\\Windows\\Temp)":
        pasta_sys_temp = Path(r"C:\Windows\Temp")
        try:
            list(pasta_sys_temp.iterdir())
        except PermissionError as exc:
            if not is_admin():
                raise PermissionError(
                    "Acesso negado em 'C:\\Windows\\Temp'. Abra o programa como Administrador."
                ) from exc
            raise
        except FileNotFoundError:
            return (0, "C:\\Windows\\Temp não encontrada", True)

        liberado, rem, ign = _limpar_pasta_conteudo(pasta_sys_temp)
        msg = f"C:\\Windows\\Temp: {rem} apagado(s)"
        if ign > 0:
            msg += f", {ign} em uso/bloqueado(s)"
        return (liberado, msg, True)

    if opcao == "Temporários do usuário (%TEMP%)":
        temp_dir = Path(os.environ.get("TEMP", Path.home() / "AppData/Local/Temp"))
        liberado, rem, ign = _limpar_pasta_conteudo(temp_dir)
        msg = f"%TEMP%: {rem} apagado(s)"
        if ign > 0:
            msg += f", {ign} em uso/bloqueado(s)"
        return (liberado, msg, True)

    if opcao == "Arquivos de Prefetch (C:\\Windows\\Prefetch)":
        pasta_prefetch = Path(r"C:\Windows\Prefetch")
        try:
            list(pasta_prefetch.iterdir())
        except PermissionError as exc:
            if not is_admin():
                raise PermissionError(
                    "Acesso negado em 'C:\\Windows\\Prefetch'. Abra o programa como Administrador."
                ) from exc
            raise
        except FileNotFoundError:
            return (0, "C:\\Windows\\Prefetch não encontrada", True)

        liberado, rem, ign = _limpar_pasta_conteudo(pasta_prefetch)
        msg = f"Prefetch: {rem} apagado(s)"
        if ign > 0:
            msg += f", {ign} em uso/bloqueado(s)"
        return (liberado, msg, True)

    if opcao == "Arquivos recentes do Windows":
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        recent_dir = appdata / "Microsoft" / "Windows" / "Recent"
        liberado, rem, ign = _limpar_pasta_conteudo(recent_dir)
        msg = f"Recentes: {rem} apagado(s)"
        if ign > 0:
            msg += f", {ign} em uso/bloqueado(s)"
        return (liberado, msg, True)

    if opcao == "Esvaziar Lixeira":
        liberado, ok, detalhe = _esvaziar_lixeira_windows()
        return (liberado, detalhe, ok)

    return (0, f"Opção desconhecida: {opcao}", False)