import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "."

Window {
    id: settingsWindow
    width: 300
    height: 200
    title: "V2M Settings"
    color: Theme.background

    // Standard window decorations for settings
    flags: Qt.Window

    Column {
        anchors.fill: parent
        anchors.margins: Theme.paddingMedium
        spacing: Theme.paddingMedium

        Text {
            text: "Settings"
            color: Theme.accent
            font.family: Theme.fontFamily
            font.pixelSize: 18
            font.bold: true
        }

        // AI Refinement Toggle
        Row {
            spacing: Theme.paddingMedium
            Switch {
                id: llmSwitch
                checked: true // TODO: Bind to config
                text: "Use AI Refinement (Gemini)"
                palette.mid: Theme.muted
                palette.windowText: Theme.accent
            }
        }

        // Model Selection
        Column {
            spacing: Theme.paddingSmall
            Text {
                text: "Whisper Model"
                color: Theme.muted
                font.family: Theme.fontFamily
            }
            ComboBox {
                model: ["distil-large-v3", "large-v3", "medium"]
                width: parent.width
            }
        }
    }
}
