import QtQuick 2.15
import QtQuick.Controls 2.15
import "."

Item {
    id: root
    width: 300
    height: 60

    property bool isRecording: Bridge.isRecording
    property bool isProcessing: Bridge.isProcessing
    property var audioLevel: Bridge.audioLevel

    Rectangle {
        id: pill
        anchors.centerIn: parent
        width: isRecording ? 300 : (isProcessing ? 150 : 12)
        height: isRecording ? 60 : (isProcessing ? 40 : 12)
        radius: height / 2
        color: Theme.background
        border.color: Theme.border
        border.width: 1

        Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
        Behavior on height { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
        Behavior on color { ColorAnimation { duration: 300 } }

        // --- Idle State (Dot) ---
        Rectangle {
            anchors.centerIn: parent
            width: 8
            height: 8
            radius: 4
            color: Theme.muted
            visible: !isRecording && !isProcessing
        }

        // --- Recording State (Waveform) ---
        Row {
            anchors.centerIn: parent
            spacing: 4
            visible: isRecording

            Repeater {
                model: 10
                Rectangle {
                    width: 4
                    height: 10 + (Math.random() * 30 * root.audioLevel) // Mock visualizer for now
                    color: Theme.accent
                    radius: 2
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        // --- Processing State (Loader) ---
        BusyIndicator {
            anchors.centerIn: parent
            running: isProcessing
            visible: isProcessing
            palette.dark: Theme.accent
        }

        // Click to toggle recording (for testing)
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                if (isRecording) {
                    Bridge.stopCapture()
                } else {
                    Bridge.startCapture()
                }
            }
        }
    }
}
