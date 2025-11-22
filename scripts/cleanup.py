#!/usr/bin/env python3
"""
Script de limpieza automática para el proyecto V2M.
Elimina archivos temporales, cache y entornos virtuales duplicados.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

# CONFIGURACIÓN / CONFIGURATION
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VENV_PRIMARY = PROJECT_ROOT / "venv"
VENV_DUPLICATE = PROJECT_ROOT / ".venv"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_RETENTION_DAYS = 7
ORPHAN_FILES = ["=1.0.3", "=4.5.0"]

class CleanupStats:
    """Estadísticas de limpieza."""
    def __init__(self):
        self.bytes_freed = 0
        self.files_deleted = 0
        self.dirs_deleted = 0

    def add_file(self, size: int):
        self.bytes_freed += size
        self.files_deleted += 1

    def add_dir(self, size: int):
        self.bytes_freed += size
        self.dirs_deleted += 1

    def to_gb(self) -> float:
        return self.bytes_freed / (1024**3)

    def report(self):
        print(f"\n{'='*60}")
        print(f"📊 REPORTE DE LIMPIEZA / CLEANUP REPORT")
        print(f"{'='*60}")
        print(f"Archivos eliminados: {self.files_deleted}")
        print(f"Directorios eliminados: {self.dirs_deleted}")
        print(f"Espacio liberado: {self.to_gb():.2f} GB")
        print(f"{'='*60}\n")


def get_dir_size(path: Path) -> int:
    """Calcula el tamaño de un directorio recursivamente."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except (PermissionError, OSError):
        pass
    return total


def clean_pycache(stats: CleanupStats, dry_run: bool = False):
    """Elimina todos los directorios __pycache__ y archivos .pyc"""
    print("🧹 Limpiando cache de Python...")

    pycache_dirs = list(PROJECT_ROOT.rglob("__pycache__"))
    pyc_files = list(PROJECT_ROOT.rglob("*.pyc"))
    pyo_files = list(PROJECT_ROOT.rglob("*.pyo"))

    total_items = len(pycache_dirs) + len(pyc_files) + len(pyo_files)

    if total_items == 0:
        print("   ✓ No hay cache Python para eliminar")
        return

    print(f"   → Encontrados {len(pycache_dirs)} dirs __pycache__, {len(pyc_files)} .pyc, {len(pyo_files)} .pyo")

    if dry_run:
        print(f"   [DRY-RUN] Se eliminarían {total_items} items")
        return

    # Eliminar directorios __pycache__
    for pycache in pycache_dirs:
        size = get_dir_size(pycache)
        try:
            shutil.rmtree(pycache)
            stats.add_dir(size)
        except Exception as e:
            print(f"   ⚠️  Error eliminando {pycache}: {e}")

    # Eliminar archivos .pyc y .pyo
    for pyc in pyc_files + pyo_files:
        try:
            size = pyc.stat().st_size
            pyc.unlink()
            stats.add_file(size)
        except Exception as e:
            print(f"   ⚠️  Error eliminando {pyc}: {e}")

    print(f"   ✓ Cache Python eliminado: {stats.dirs_deleted} dirs, {stats.files_deleted} archivos")


def clean_duplicate_venv(stats: CleanupStats, dry_run: bool = False):
    """Elimina el entorno virtual duplicado .venv si venv está en uso."""
    print("\n🔧 Validando entornos virtuales...")

    if not VENV_DUPLICATE.exists():
        print("   ✓ No existe .venv duplicado")
        return

    if not VENV_PRIMARY.exists():
        print("   ⚠️  ADVERTENCIA: venv primario no existe, conservando .venv")
        return

    # Verificar que venv está en uso por systemd
    try:
        result = subprocess.run(
            ["systemctl", "--user", "show", "v2m.service", "-p", "ExecStart"],
            capture_output=True,
            text=True,
            check=False
        )
        if str(VENV_PRIMARY) not in result.stdout:
            print(f"   ⚠️  ADVERTENCIA: v2m.service no usa {VENV_PRIMARY}")
            print(f"      Saltando eliminación de .venv por seguridad")
            return
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar systemd service: {e}")
        print(f"      Saltando eliminación de .venv por seguridad")
        return

    size = get_dir_size(VENV_DUPLICATE)
    size_gb = size / (1024**3)

    print(f"   → .venv duplicado encontrado: {size_gb:.2f} GB")

    if dry_run:
        print(f"   [DRY-RUN] Se eliminaría .venv ({size_gb:.2f} GB)")
        return

    try:
        shutil.rmtree(VENV_DUPLICATE)
        stats.add_dir(size)
        print(f"   ✓ .venv eliminado: {size_gb:.2f} GB liberados")
    except Exception as e:
        print(f"   ❌ Error eliminando .venv: {e}")


def rotate_logs(stats: CleanupStats, dry_run: bool = False):
    """Elimina logs antiguos (>7 días)."""
    print(f"\n📋 Rotando logs (retención: {LOG_RETENTION_DAYS} días)...")

    if not LOGS_DIR.exists():
        print("   ✓ Directorio de logs no existe")
        return

    cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    old_logs = []

    for log_file in LOGS_DIR.glob("*.log"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime < cutoff_date:
            old_logs.append(log_file)

    if not old_logs:
        print("   ✓ No hay logs antiguos para eliminar")
        return

    print(f"   → Encontrados {len(old_logs)} logs antiguos")

    if dry_run:
        for log in old_logs:
            print(f"   [DRY-RUN] Se eliminaría: {log.name}")
        return

    for log in old_logs:
        try:
            size = log.stat().st_size
            log.unlink()
            stats.add_file(size)
            print(f"   ✓ Eliminado: {log.name}")
        except Exception as e:
            print(f"   ⚠️  Error eliminando {log.name}: {e}")


def remove_orphans(stats: CleanupStats, dry_run: bool = False):
    """Elimina archivos huérfanos detectados."""
    print("\n🗑️  Eliminando archivos huérfanos...")

    found_orphans = []
    for orphan in ORPHAN_FILES:
        orphan_path = PROJECT_ROOT / orphan
        if orphan_path.exists():
            found_orphans.append(orphan_path)

    if not found_orphans:
        print("   ✓ No hay archivos huérfanos")
        return

    print(f"   → Encontrados {len(found_orphans)} archivos huérfanos")

    for orphan in found_orphans:
        size = orphan.stat().st_size if orphan.is_file() else get_dir_size(orphan)

        if dry_run:
            print(f"   [DRY-RUN] Se eliminaría: {orphan.name}")
            continue

        try:
            if orphan.is_file():
                orphan.unlink()
                stats.add_file(size)
            else:
                shutil.rmtree(orphan)
                stats.add_dir(size)
            print(f"   ✓ Eliminado: {orphan.name}")
        except Exception as e:
            print(f"   ⚠️  Error eliminando {orphan.name}: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Script de limpieza automática para V2M",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 scripts/cleanup.py --dry-run    # Ver qué se eliminaría
  python3 scripts/cleanup.py --all        # Limpieza completa
  python3 scripts/cleanup.py --cache      # Solo cache Python
  python3 scripts/cleanup.py --fix-venv   # Solo .venv duplicado
        """
    )

    parser.add_argument("--dry-run", action="store_true",
                       help="Mostrar qué se eliminaría sin hacer cambios")
    parser.add_argument("--all", action="store_true",
                       help="Ejecutar todas las operaciones de limpieza")
    parser.add_argument("--cache", action="store_true",
                       help="Limpiar solo cache Python (__pycache__, .pyc)")
    parser.add_argument("--fix-venv", action="store_true",
                       help="Eliminar solo .venv duplicado")
    parser.add_argument("--logs", action="store_true",
                       help="Rotar solo logs antiguos")
    parser.add_argument("--orphans", action="store_true",
                       help="Eliminar solo archivos huérfanos")

    args = parser.parse_args()

    # Si no se especifica nada, mostrar ayuda
    if not any([args.all, args.cache, args.fix_venv, args.logs, args.orphans]):
        parser.print_help()
        return

    stats = CleanupStats()

    print("\n" + "="*60)
    print("🧹 LIMPIEZA V2M / V2M CLEANUP")
    if args.dry_run:
        print("   [MODO DRY-RUN - NO SE HARÁN CAMBIOS]")
    print("="*60 + "\n")

    # Ejecutar operaciones seleccionadas
    if args.all or args.cache:
        clean_pycache(stats, args.dry_run)

    if args.all or args.fix_venv:
        clean_duplicate_venv(stats, args.dry_run)

    if args.all or args.logs:
        rotate_logs(stats, args.dry_run)

    if args.all or args.orphans:
        remove_orphans(stats, args.dry_run)

    # Reporte final
    if not args.dry_run:
        stats.report()
    else:
        print("\n[DRY-RUN] Ejecuta sin --dry-run para aplicar cambios\n")


if __name__ == "__main__":
    main()
