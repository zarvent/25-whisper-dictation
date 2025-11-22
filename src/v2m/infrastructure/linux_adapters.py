import subprocess
import os
import time
from pathlib import Path
from typing import Optional, Tuple
from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger


class LinuxClipboardAdapter(ClipboardInterface):
    """
    Adaptador de portapapeles para Linux que usa directamente xclip o wl-clipboard.

    No depende de PYPERCLIP para evitar problemas con variables de entorno
    en procesos daemon. Detecta automáticamente X11 vs Wayland.
    """

    def __init__(self):
        self._backend: Optional[str] = None
        self._env: dict = {}
        self._detect_environment()

    def _find_xauthority(self) -> Optional[str]:
        """Busca el archivo .Xauthority en ubicaciones estándar."""
        # 1. Si ya está en el entorno, usarlo
        if os.environ.get("XAUTHORITY"):
            return os.environ["XAUTHORITY"]

        # 2. Ubicación estándar en home
        home = Path(os.environ.get("HOME", subprocess.getoutput("echo ~")))
        xauth = home / ".Xauthority"
        if xauth.exists():
            return str(xauth)

        # 3. Ubicación en /run/user (común en GDM/systemd)
        try:
            uid = os.getuid()
            run_user_auth = Path(f"/run/user/{uid}/gdm/Xauthority")
            if run_user_auth.exists():
                return str(run_user_auth)
        except Exception:
            pass

        return None

    def _detect_environment(self) -> None:
        """
        Detecta variables de entorno buscando sesiones GRÁFICAS.
        Estrategia: Env Vars > Loginctl > Sockets en /tmp/.X11-unix
        """
        # 1. Heredar del entorno actual (Prioridad máxima)
        if self._try_inherit_from_environment():
            return

        # 2. Scavenging vía loginctl
        if self._try_detect_via_loginctl():
            return

        # 3. FALLBACK ULTIMATE: Escanear sockets activos en /tmp/.X11-unix
        if self._try_detect_via_socket_scan():
            return

        # 4. No se encontró ningún display gráfico
        logger.error("CRITICAL: No graphical display found. Clipboard will not work.")
        self._backend = "x11"
        self._env = {}

    def _try_inherit_from_environment(self) -> bool:
        """Intenta heredar variables de entorno del proceso actual."""
        if os.environ.get("WAYLAND_DISPLAY"):
            self._backend = "wayland"
            self._env = {"WAYLAND_DISPLAY": os.environ["WAYLAND_DISPLAY"]}
            return True
        
        if os.environ.get("DISPLAY"):
            self._backend = "x11"
            self._env = {"DISPLAY": os.environ["DISPLAY"]}
            return True
        
        return False

    def _try_detect_via_loginctl(self) -> bool:
        """Intenta detectar el entorno gráfico usando loginctl."""
        try:
            user = os.environ.get("USER") or subprocess.getoutput("whoami")
            cmd = f"loginctl list-sessions --no-legend | grep {user} | awk '{{print $1}}'"
            sessions = subprocess.check_output(cmd, shell=True, text=True).strip().split('\n')

            for session_id in sessions:
                if not session_id:
                    continue

                if self._try_configure_from_session(session_id):
                    return True

        except Exception as e:
            logger.warning(f"Environment scavenging failed: {e}")

        return False

    def _try_configure_from_session(self, session_id: str) -> bool:
        """Configura el entorno desde una sesión loginctl específica."""
        try:
            type_cmd = ["loginctl", "show-session", session_id, "-p", "Type", "--value"]
            session_type = subprocess.check_output(type_cmd, text=True).strip()

            display_cmd = ["loginctl", "show-session", session_id, "-p", "Display", "--value"]
            display_val = subprocess.check_output(display_cmd, text=True).strip()

            if not display_val:
                return False

            self._backend = "wayland" if session_type == "wayland" else "x11"
            
            if session_type == "wayland":
                self._env = {"WAYLAND_DISPLAY": display_val}
            else:
                self._env = {"DISPLAY": display_val}
                xauth_path = self._find_xauthority()
                if xauth_path:
                    self._env["XAUTHORITY"] = xauth_path
                    logger.info(f"XAUTHORITY scavenged: {xauth_path}")

            logger.info(f"Environment detected via loginctl: Session {session_id} ({session_type}) -> {display_val}")
            return True

        except Exception:
            return False

    def _try_detect_via_socket_scan(self) -> bool:
        """Intenta detectar X11 escaneando sockets en /tmp/.X11-unix."""
        try:
            x11_socket_dir = Path("/tmp/.X11-unix")
            if not x11_socket_dir.exists():
                return False

            sockets = sorted([s.name for s in x11_socket_dir.iterdir() if s.name.startswith("X")])
            if not sockets:
                return False

            active_display = f":{sockets[0][1:]}"
            self._backend = "x11"
            self._env = {"DISPLAY": active_display}
            logger.info(f"Display detected via socket scan: {active_display}")

            xauth = self._find_xauthority()
            if xauth:
                self._env["XAUTHORITY"] = xauth
            
            return True

        except Exception as e:
            logger.warning(f"Socket scan failed: {e}")
            return False

    def _get_clipboard_commands(self) -> Tuple[list, list]:
        """
        Retorna los comandos para copiar y pegar según el backend detectado.

        Returns:
            Tupla con (comando_copy, comando_paste)
        """
        if self._backend == "wayland":
            return (
                ["wl-copy"],
                ["wl-paste"]
            )
        else:  # x11
            return (
                ["xclip", "-selection", "clipboard"],
                ["xclip", "-selection", "clipboard", "-out"]
            )

    def copy(self, text: str) -> None:
        if not text: return
        copy_cmd, _ = self._get_clipboard_commands()

        try:
            env = os.environ.copy()
            env.update(self._env)

            process = subprocess.Popen(
                copy_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, # Capturamos stderr
                env=env
            )

            process.stdin.write(text.encode("utf-8"))
            process.stdin.close()

            # Espera táctica y verificación de estado
            time.sleep(0.1)
            exit_code = process.poll()

            if exit_code is not None and exit_code != 0:
                # El proceso murió prematuramente
                stderr_out = process.stderr.read().decode()
                logger.error(f"Clipboard process died with code {exit_code}. STDERR: {stderr_out}")
            else:
                logger.debug(f"Copied {len(text)} chars to clipboard (PID: {process.pid})")

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")

    def paste(self) -> str:
        """
        Obtiene texto del portapapeles del sistema.

        Returns:
            Contenido del portapapeles o cadena vacía si falla.
        """
        _, paste_cmd = self._get_clipboard_commands()

        try:
            # Combinar env del sistema con las variables detectadas
            env = os.environ.copy()
            env.update(self._env)

            result = subprocess.run(
                paste_cmd,
                capture_output=True,
                env=env,
                timeout=2
            )

            if result.returncode != 0:
                logger.error(f"Clipboard paste failed: {result.stderr.decode('utf-8', errors='ignore')}")
                return ""

            return result.stdout.decode("utf-8", errors="ignore")

        except FileNotFoundError:
            logger.error(f"Clipboard tool not found: {paste_cmd[0]}. Install xclip or wl-clipboard.")
            return ""
        except subprocess.TimeoutExpired:
            logger.error("Clipboard paste operation timed out")
            return ""
        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return ""

class LinuxNotificationAdapter(NotificationInterface):
    def notify(self, title: str, message: str) -> None:
        try:
            # usando notify-send ya que es estándar en la mayoría de los de de linux
            subprocess.run(
                ["notify-send", title, message],
                check=False,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            logger.warning("notify-send not found, notification skipped")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
