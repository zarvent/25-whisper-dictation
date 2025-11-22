import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import "."  // Import local components (Theme)

Window {
    id: mainWindow
    visible: true
    width: 400
    height: 300
    title: "V2M Onyx - Voice to Machine"
    color: Theme.background

    // Ventana normal con decoraciones para que sea visible
    flags: Qt.Window

    Column {
        anchors.fill: parent
        anchors.margins: Theme.paddingLarge
        spacing: Theme.paddingLarge

        // --- Header ---
        Text {
            text: "🎤 V2M ONYX"
            color: Theme.accent
            font.family: Theme.fontFamily
            font.pixelSize: 24
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }

        // --- Estado ---
        Rectangle {
            width: parent.width
            height: 80
            color: Theme.surface
            radius: Theme.radius
            border.color: Theme.border
            border.width: 1

            Column {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    text: {
                        if (Bridge.isRecording) return "🔴 ESCUCHANDO..."
                        return "⚪ Listo para grabar"
                    }
                    color: Bridge.isRecording ? "#FF4444" : Theme.accent
                    font.family: Theme.fontFamily
                    font.pixelSize: 18
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    text: {
                        if (Bridge.isRecording) return "Habla hasta que detecte silencio..."
                        return "Click para iniciar captura inteligente"
                    }
                    color: Theme.muted
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }

        // --- Botón Principal ---
        Button {
            id: mainButton
            width: parent.width
            height: 80
            enabled: !Bridge.isRecording

            background: Rectangle {
                color: mainButton.pressed ? Theme.border : (Bridge.isRecording ? "#888888" : "#44AA44")
                radius: Theme.radius
                border.color: Theme.accent
                border.width: 2
            }

            contentItem: Text {
                text: Bridge.isRecording ? "⏱️ ESCUCHANDO..." : "🎤 INICIAR CAPTURA"
                color: Theme.accent
                font.family: Theme.fontFamily
                font.pixelSize: 24
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                if (!Bridge.isRecording) {
                    Bridge.startCapture()
                }
            }
        }

        // --- Info adicional ---
        Text {
            text: "La transcripción se copia automáticamente al portapapeles"
            color: Theme.muted
            font.family: Theme.fontFamily
            font.pixelSize: 10
            wrapMode: Text.WordWrap
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
        }
    }

    // Conexión a señales del Bridge
    Connections {
        target: Bridge
        function onTranscriptionReceived(text) {
            console.log("Transcripción recibida:", text)
        }
        function onErrorOccurred(error) {
            console.log("Error:", error)
        }
    }
}
