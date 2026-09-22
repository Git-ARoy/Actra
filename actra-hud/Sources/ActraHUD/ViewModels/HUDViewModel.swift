import Foundation
import SwiftUI
import Combine

public class HUDViewModel: ObservableObject, SocketClientDelegate {
    @Published public var isConnected: Bool = false
    @Published public var currentTask: TaskUpdateMessage? = nil
    @Published public var activeConfirmation: ConfirmationRequestMessage? = nil
    @Published public var health: HealthStatusMessage? = nil
    @Published public var activeAlert: SystemAlertMessage? = nil
    @Published public var taskHistory: [TaskUpdateMessage] = []

    private let socketClient: SocketClient

    public init(socketPath: String = "/tmp/actra_hud.sock") {
        self.socketClient = SocketClient(socketPath: socketPath)
        self.socketClient.delegate = self
        self.socketClient.start()
    }

    deinit {
        socketClient.stop()
    }

    // ------------------------------------------------------------------
    // SocketClientDelegate
    // ------------------------------------------------------------------

    public func socketClientDidConnect() {
        self.isConnected = true
    }

    public func socketClientDidDisconnect() {
        self.isConnected = false
    }

    public func socketClientReceived(taskUpdate: TaskUpdateMessage) {
        self.currentTask = taskUpdate
        if !taskHistory.contains(where: { $0.task_id == taskUpdate.task_id }) {
            taskHistory.insert(taskUpdate, at: 0)
        } else if let index = taskHistory.firstIndex(where: { $0.task_id == taskUpdate.task_id }) {
            taskHistory[index] = taskUpdate
        }
    }

    public func socketClientReceived(confirmationRequest: ConfirmationRequestMessage) {
        self.activeConfirmation = confirmationRequest
    }

    public func socketClientReceived(healthStatus: HealthStatusMessage) {
        self.health = healthStatus
    }

    public func socketClientReceived(systemAlert: SystemAlertMessage) {
        self.activeAlert = systemAlert
    }

    // ------------------------------------------------------------------
    // Confirmation Actions
    // ------------------------------------------------------------------

    public func approveConfirmation() {
        guard let conf = activeConfirmation else { return }
        let response = ConfirmationResponseMessage(id: conf.id, approved: true, reason: "Approved by user on HUD")
        socketClient.send(confirmationResponse: response)
        self.activeConfirmation = nil
    }

    public func denyConfirmation() {
        guard let conf = activeConfirmation else { return }
        let response = ConfirmationResponseMessage(id: conf.id, approved: false, reason: "Denied by user on HUD")
        socketClient.send(confirmationResponse: response)
        self.activeConfirmation = nil
    }

    public func dismissAlert() {
        self.activeAlert = nil
    }

    public func reconnect() {
        socketClient.reconnectNow()
    }

    public func submitGoal(_ goalText: String) {
        let trimmed = goalText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        let cmd = UserCommandMessage(action: "submit_goal", payload: ["goal": trimmed])
        socketClient.send(command: cmd)
    }

    public func triggerTestConfirmation() {
        let mockArgs: [String: AnyCodable] = [
            "path": AnyCodable("/Users/aroy/Documents/sensitive_data.txt"),
            "overwrite": AnyCodable(true)
        ]
        self.activeConfirmation = ConfirmationRequestMessage(
            id: "test_\(UUID().uuidString.prefix(6))",
            tool: "delete_file",
            arguments: mockArgs,
            safety_level: "DANGEROUS",
            details: "Simulated confirmation test on HUD"
        )
    }
}
