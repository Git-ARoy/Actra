import SwiftUI
import AppKit

class FloatingHUDPanel: NSPanel {
    override var canBecomeKey: Bool {
        return true
    }

    override var canBecomeMain: Bool {
        return true
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: FloatingHUDPanel?
    let viewModel = HUDViewModel()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Ensure macOS treats this as a regular active GUI application capable of receiving focus
        NSApp.setActivationPolicy(.regular)

        let contentView = HUDView(viewModel: viewModel)

        let panel = FloatingHUDPanel(
            contentRect: NSRect(x: 0, y: 0, width: 380, height: 460),
            styleMask: [.titled, .closable, .miniaturizable, .fullSizeContentView, .utilityWindow],
            backing: .buffered,
            defer: false
        )

        panel.title = "Actra HUD"
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.isFloatingPanel = true
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true
        panel.isReleasedWhenClosed = false
        panel.backgroundColor = .clear
        panel.isOpaque = false
        panel.hasShadow = false // Shadow is rendered inside SwiftUI GlassCard / container
        panel.acceptsMouseMovedEvents = true

        let hostingView = NSHostingView(rootView: contentView)
        panel.contentView = hostingView

        // Position on top-right of the main screen
        if let screen = NSScreen.main {
            let visibleFrame = screen.visibleFrame
            let x = visibleFrame.maxX - 400
            let y = visibleFrame.maxY - 480
            panel.setFrameOrigin(NSPoint(x: x, y: y))
        } else {
            panel.center()
        }

        panel.makeKeyAndOrderFront(nil)
        self.window = panel

        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

@main
struct ActraHUDApp {
    static func main() {
        let app = NSApplication.shared
        let delegate = AppDelegate()
        app.delegate = delegate
        app.run()
    }
}
