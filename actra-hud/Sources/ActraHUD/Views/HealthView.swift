import SwiftUI

public struct HealthView: View {
    let health: HealthStatusMessage?

    public var body: some View {
        HStack(spacing: 14) {
            HStack(spacing: 4) {
                Circle()
                    .fill((health?.llm_status == "connected" || health?.llm_status == "ok") ? Color.green : Color.orange)
                    .frame(width: 8, height: 8)
                Text("LLM: \(health?.llm_status.capitalized ?? "Offline")")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if let cpu = health?.cpu_percent, cpu > 0 {
                HStack(spacing: 3) {
                    Image(systemName: "cpu")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(String(format: "%.1f%%", cpu))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            if let mem = health?.memory_percent, mem > 0 {
                HStack(spacing: 3) {
                    Image(systemName: "memorychip")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(String(format: "%.1f%%", mem))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
}
