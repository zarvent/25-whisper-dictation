import sys
import os
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from v2m.gui.bridge import Bridge

def main():
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("Zarvent")
    app.setOrganizationDomain("zarvent.com")
    app.setApplicationName("V2M Onyx")

    engine = QQmlApplicationEngine()

    # Initialize Bridge
    bridge = Bridge()
    engine.rootContext().setContextProperty("Bridge", bridge)

    # Add current directory to import path so Theme.qml is found
    current_dir = Path(__file__).parent
    engine.addImportPath(str(current_dir))

    qml_file = current_dir / "main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
