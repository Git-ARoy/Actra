import Foundation

public struct TaskUpdateMessage: Codable, Identifiable {
    public var id: String { task_id }
    public let task_id: String
    public let goal: String
    public let status: String
    public let step_index: Int
    public let step_description: String
    public let progress_percent: Double
    public let retries: Int
    public let block_reason: String?
    public let timestamp: String
    public let type: String
}

public struct ConfirmationRequestMessage: Codable, Identifiable {
    public let id: String
    public let tool: String
    public let arguments: [String: AnyCodable]
    public let safety_level: String
    public let details: String
    public let timestamp: String
    public let type: String

    public init(id: String, tool: String, arguments: [String: AnyCodable], safety_level: String, details: String = "", timestamp: String = "") {
        self.id = id
        self.tool = tool
        self.arguments = arguments
        self.safety_level = safety_level
        self.details = details
        self.timestamp = timestamp
        self.type = "confirmation_request"
    }
}

public struct ConfirmationResponseMessage: Codable {
    public let id: String
    public let approved: Bool
    public let reason: String
    public let type: String

    public init(id: String, approved: Bool, reason: String = "") {
        self.id = id
        self.approved = approved
        self.reason = reason
        self.type = "confirmation_response"
    }
}

public struct HealthStatusMessage: Codable {
    public let llm_status: String
    public let cpu_percent: Double
    public let memory_percent: Double
    public let active_tasks: Int
    public let timestamp: String
    public let type: String
}

public struct SystemAlertMessage: Codable, Identifiable {
    public var id: String { alert_id }
    public let alert_id: String
    public let severity: String
    public let title: String
    public let message: String
    public let timestamp: String
    public let type: String
}

public struct UserCommandMessage: Codable {
    public let action: String
    public let payload: [String: String]
    public let type: String

    public init(action: String, payload: [String: String] = [:]) {
        self.action = action
        self.payload = payload
        self.type = "user_command"
    }
}

// Helper for dynamic dictionary decoding
public struct AnyCodable: Codable, CustomStringConvertible {
    public let value: Any

    public var description: String {
        return "\(value)"
    }

    public init(_ value: Any) {
        self.value = value
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self.value = ""
        } else if let bool = try? container.decode(Bool.self) {
            self.value = bool
        } else if let int = try? container.decode(Int.self) {
            self.value = int
        } else if let double = try? container.decode(Double.self) {
            self.value = double
        } else if let string = try? container.decode(String.self) {
            self.value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            self.value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            self.value = dict.mapValues { $0.value }
        } else {
            self.value = ""
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let bool = value as? Bool {
            try container.encode(bool)
        } else if let int = value as? Int {
            try container.encode(int)
        } else if let double = value as? Double {
            try container.encode(double)
        } else if let string = value as? String {
            try container.encode(string)
        } else {
            try container.encode("\(value)")
        }
    }
}
