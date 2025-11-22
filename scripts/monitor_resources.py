#!/usr/bin/env python3
"""
Script de monitoreo de recursos para V2M.
Genera reporte del consumo de memoria, GPU, disco y procesos activos.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VENV_DIR = PROJECT_ROOT / "venv"
LOGS_DIR = PROJECT_ROOT / "logs"


def get_process_info():
    """Obtiene información del daemon V2M."""
    print("## PROCESOS V2M / V2M PROCESSES\n")

    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )

        # Filtrar procesos relacionados con V2M
        v2m_processes = [line for line in result.stdout.split('\n')
                         if 'v2m' in line.lower() and 'grep' not in line]

        if v2m_processes:
            print("```")
            print(result.stdout.split('\n')[0])  # Header
            for proc in v2m_processes:
                print(proc)
            print("```\n")
        else:
            print("⚠️  No se encontraron procesos V2M activos\n")

    except Exception as e:
        print(f"❌ Error obteniendo procesos: {e}\n")


def get_daemon_memory():
    """Obtiene uso de memoria del daemon."""
    print("## MEMORIA DEL DAEMON / DAEMON MEMORY\n")

    try:
        # Obtener PID del daemon desde systemd
        result = subprocess.run(
            ["systemctl", "--user", "show", "v2m.service", "-p", "MainPID"],
            capture_output=True,
            text=True,
            check=True
        )

        pid = result.stdout.split('=')[1].strip()

        if pid == "0":
            print("⚠️  Daemon no está corriendo\n")
            return

        # Obtener memoria del proceso
        status_result = subprocess.run(
            ["systemctl", "--user", "status", "v2m.service", "--no-pager"],
            capture_output=True,
            text=True,
            check=False
        )

        # Extraer línea de Memory
        for line in status_result.stdout.split('\n'):
            if 'Memory:' in line:
                print(f"**PID**: {pid}")
                print(f"**{line.strip()}**\n")
                break

    except Exception as e:
        print(f"❌ Error obteniendo memoria del daemon: {e}\n")


def get_gpu_usage():
    """Obtiene uso de GPU (NVIDIA)."""
    print("## USO DE GPU / GPU USAGE\n")

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )

        gpu_info = result.stdout.strip().split(', ')

        print(f"**GPU**: {gpu_info[0]}")
        print(f"**VRAM**: {gpu_info[1]} MB / {gpu_info[2]} MB ({int(gpu_info[1])/int(gpu_info[2])*100:.1f}%)")
        print(f"**Utilización**: {gpu_info[3]}%\n")

    except FileNotFoundError:
        print("⚠️  nvidia-smi no disponible (GPU no detectada)\n")
    except Exception as e:
        print(f"❌ Error obteniendo info de GPU: {e}\n")


def get_disk_usage():
    """Obtiene uso de disco del proyecto."""
    print("## USO DE DISCO / DISK USAGE\n")

    try:
        result = subprocess.run(
            ["du", "-sh", str(PROJECT_ROOT / "*")],
            capture_output=True,
            text=True,
            shell=True,
            check=False
        )

        lines = result.stdout.strip().split('\n')
        sorted_lines = sorted(lines, key=lambda x: x.split()[0], reverse=True)

        print("```")
        for line in sorted_lines[:10]:  # Top 10
            print(line)
        print("```\n")

        # Tamaño total
        total_result = subprocess.run(
            ["du", "-sh", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            check=True
        )

        print(f"**TOTAL**: {total_result.stdout.split()[0]}\n")

    except Exception as e:
        print(f"❌ Error obteniendo uso de disco: {e}\n")


def check_cache_bloat():
    """Cuenta directorios __pycache__ y archivos .pyc."""
    print("## CACHE PYTHON / PYTHON CACHE\n")

    try:
        pycache_result = subprocess.run(
            ["find", str(PROJECT_ROOT), "-type", "d", "-name", "__pycache__"],
            capture_output=True,
            text=True,
            check=True
        )

        pyc_result = subprocess.run(
            ["find", str(PROJECT_ROOT), "-name", "*.pyc"],
            capture_output=True,
            text=True,
            check=True
        )

        pycache_count = len([l for l in pycache_result.stdout.strip().split('\n') if l])
        pyc_count = len([l for l in pyc_result.stdout.strip().split('\n') if l])

        print(f"**Directorios `__pycache__`**: {pycache_count}")
        print(f"**Archivos `.pyc`**: {pyc_count}")

        if pycache_count > 100 or pyc_count > 1000:
            print("\n⚠️  **ADVERTENCIA**: Cache excesivo detectado")
            print(f"   Ejecuta: `python3 scripts/cleanup.py --cache`\n")
        else:
            print("\n✓ Cache dentro de límites normales\n")

    except Exception as e:
        print(f"❌ Error contando cache: {e}\n")


def generate_report():
    """Genera reporte completo en markdown."""

    print("\n" + "="*70)
    print(f"# REPORTE DE RECURSOS V2M / V2M RESOURCE REPORT")
    print(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    get_process_info()
    get_daemon_memory()
    get_gpu_usage()
    get_disk_usage()
    check_cache_bloat()

    print("="*70)
    print("## ACCIONES RECOMENDADAS / RECOMMENDED ACTIONS\n")
    print("- **Limpieza completa**: `python3 scripts/cleanup.py --all`")
    print("- **Solo cache**: `python3 scripts/cleanup.py --cache`")
    print("- **Reiniciar daemon**: `systemctl --user restart v2m.service`")
    print("- **Ver logs**: `journalctl --user -u v2m.service -n 50`")
    print("="*70 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitoreo de recursos del proyecto V2M"
    )

    parser.add_argument("--save", type=str, metavar="FILE",
                       help="Guardar reporte en archivo markdown")

    args = parser.parse_args()

    if args.save:
        # Redirigir stdout a archivo
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            generate_report()

        output = f.getvalue()

        with open(args.save, 'w') as out:
            out.write(output)

        print(f"✓ Reporte guardado en: {args.save}")
    else:
        generate_report()


if __name__ == "__main__":
    main()
