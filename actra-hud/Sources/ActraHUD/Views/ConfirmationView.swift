import SwiftUI

public struct ConfirmationView: View {
    let request: ConfirmationRequestMessage
    let onApprove: () -> Void
    let onDeny: () -> Void

    private var safetyBadgeColor: Color {
        switch request.safety_level.uppercased() {
        case "DANGEROUS":
            return .red
        case "SENSITIVE":
            return .orange
        default:
            return .blue
        }
    }

    public var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "exclamationmark.shield.fill")
                        .foregroundColor(safetyBadgeColor)
                        .font(.title2)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Safety Confirmation Required")
                            .font(.headline)
                            .foregroundColor(.primary)

                        Text("Tier: \(request.safety_level)")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(safetyBadgeColor)
                    }

                    Spacer()
                }

                Divider()

                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Tool:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        Text(request.tool)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .fontDesign(.monospaced)
                    }

                    if !request.arguments.isEmpty {
                        Text("Arguments:")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        VStack(alignment: .leading, spacing: 2) {
                            ForEach(Array(request.arguments.keys.sorted()), id: \.self) { key in
                                HStack(alignment: .top) {
                                    Text("• \(key):")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Text("\(request.arguments[key]?.description ?? "")")
                                        .font(.caption)
                                        .fontDesign(.monospaced)
                                        .foregroundColor(.primary)
                                        .lineLimit(2)
                                }
                            }
                        }
                        .padding(8)
                        .background(Color.black.opacity(0.2))
                        .cornerRadius(8)
                    }
                }

                HStack(spacing: 12) {
                    Button(action: onDeny) {
                        Label("Deny", systemImage: "xmark.circle.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .tint(.red)
                    .keyboardShortcut(.cancelAction)

                    Button(action: onApprove) {
                        Label("Approve", systemImage: "checkmark.circle.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.green)
                    .keyboardShortcut(.defaultAction)
                }
                .padding(.top, 4)
            }
        }
    }
}
