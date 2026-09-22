import Foundation
import Network

public protocol SocketClientDelegate: AnyObject {
    func socketClientDidConnect()
    func socketClientDidDisconnect()
    func socketClientReceived(taskUpdate: TaskUpdateMessage)
    func socketClientReceived(confirmationRequest: ConfirmationRequestMessage)
    func socketClientReceived(healthStatus: HealthStatusMessage)
    func socketClientReceived(systemAlert: SystemAlertMessage)
}

public class SocketClient {
    public let socketPath: String
    public weak var delegate: SocketClientDelegate?

    private var connection: NWConnection?
    private let queue = DispatchQueue(label: "com.actra.hud.socket", qos: .userInitiated)
    private var isRunning = false
    private var buffer = Data()

    public init(socketPath: String = "/tmp/actra_hud.sock") {
        self.socketPath = socketPath
    }

    public func start() {
        isRunning = true
        connect()
    }

    public func stop() {
        isRunning = false
        connection?.cancel()
        connection = nil
    }

    public func reconnectNow() {
        connection?.cancel()
        connection = nil
        connect()
    }

    private func connect() {
        guard isRunning else { return }

        let endpoint = NWEndpoint.unix(path: socketPath)
        let params = NWParameters.tcp
        let conn = NWConnection(to: endpoint, using: params)
        self.connection = conn

        conn.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            switch state {
            case .ready:
                DispatchQueue.main.async {
                    self.delegate?.socketClientDidConnect()
                }
                self.receiveLoop()
            case .failed, .cancelled:
                DispatchQueue.main.async {
                    self.delegate?.socketClientDidDisconnect()
                }
                self.scheduleReconnect()
            default:
                break
            }
        }

        conn.start(queue: queue)
    }

    private func scheduleReconnect() {
        guard isRunning else { return }
        queue.asyncAfter(deadline: .now() + 1.5) { [weak self] in
            guard let self = self, self.isRunning else { return }
            self.connect()
        }
    }

    private func receiveLoop() {
        guard let conn = connection, conn.state == .ready else { return }

        conn.receive(minimumIncompleteLength: 1, maximumLength: 65536) { [weak self] content, _, isComplete, error in
            guard let self = self else { return }

            if let data = content, !data.isEmpty {
                self.buffer.append(data)
                self.processBuffer()
            }

            if isComplete || error != nil {
                self.scheduleReconnect()
            } else {
                self.receiveLoop()
            }
        }
    }

    private func processBuffer() {
        let newline = Data([0x0A]) // 

        while let range = buffer.range(of: newline) {
            let lineData = buffer.subdata(in: 0..<range.lowerBound)
            buffer.removeSubrange(0..<range.upperBound)

            guard !lineData.isEmpty else { continue }
            handleMessageData(lineData)
        }
    }

    private func handleMessageData(_ data: Data) {
        guard let jsonObject = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = jsonObject["type"] as? String else {
            return
        }

        let decoder = JSONDecoder()

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            switch type {
            case "task_update":
                if let msg = try? decoder.decode(TaskUpdateMessage.self, from: data) {
                    self.delegate?.socketClientReceived(taskUpdate: msg)
                }
            case "confirmation_request":
                if let msg = try? decoder.decode(ConfirmationRequestMessage.self, from: data) {
                    self.delegate?.socketClientReceived(confirmationRequest: msg)
                }
            case "health_status":
                if let msg = try? decoder.decode(HealthStatusMessage.self, from: data) {
                    self.delegate?.socketClientReceived(healthStatus: msg)
                }
            case "system_alert":
                if let msg = try? decoder.decode(SystemAlertMessage.self, from: data) {
                    self.delegate?.socketClientReceived(systemAlert: msg)
                }
            default:
                break
            }
        }
    }

    public func send(confirmationResponse: ConfirmationResponseMessage) {
        guard let conn = connection, conn.state == .ready else { return }
        let encoder = JSONEncoder()
        if var data = try? encoder.encode(confirmationResponse) {
            data.append(Data([0x0A])) // 

            conn.send(content: data, completion: .contentProcessed({ error in
                if let error = error {
                    print("Error sending confirmation response: \(error)")
                }
            }))
        }
    }

    public func send(command: UserCommandMessage) {
        guard let conn = connection, conn.state == .ready else { return }
        let encoder = JSONEncoder()
        if var data = try? encoder.encode(command) {
            data.append(Data([0x0A])) // 

            conn.send(content: data, completion: .contentProcessed({ error in
                if let error = error {
                    print("Error sending command: \(error)")
                }
            }))
        }
    }
}
