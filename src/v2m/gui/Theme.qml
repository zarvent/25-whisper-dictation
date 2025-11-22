pragma Singleton
import QtQuick 2.15

QtObject {
    // Colors
    readonly property color background: "#191919"
    readonly property color surface: "#202020"
    readonly property color border: "#333333"
    readonly property color accent: "#FFFFFF"
    readonly property color muted: "#888888"
    readonly property color error: "#FF4444"
    readonly property color success: "#44FF44"

    // Fonts
    readonly property string fontFamily: "Inter, SF Pro Display, Roboto, sans-serif"

    // Spacing
    readonly property int paddingSmall: 8
    readonly property int paddingMedium: 16
    readonly property int paddingLarge: 24

    readonly property int radius: 8
}
