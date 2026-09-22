import SwiftUI

public struct HUDView: View {
    @ObservedObject var viewModel: HUDViewModel
    @State private var goalInput: String = ""

    private var statusColor: Color {
        guard let status = viewModel.currentTask?.status else { return .secondary }
        switch status {
        case "RECEIVED", "PLANNING":
            return .blue
        case "EXECUTING":
            return .purple
        case "OBSERVING", "VERIFYING":
            return .teal
        case "AUTHENTICATING":
            return .indigo
        case "WAITING_FOR_CONFIRMATION", "BLOCKED":
            return .orange
        case "SYSTEM_ALERT":
            return .yellow
        case "COMPLETED":
            return .green
        case "FAILED", "CANCELLED":
            return .red
        default:
            return .secondary
        }
    }

    public var body: some View {
        VStack(spacing: 12) {
            headerSection
            alertSection
            contentSection
            footerSection
        }
        .padding(16)
        .frame(width: 380)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(Color.white.opacity(0.2), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.35), radius: 24, x: 0, y: 12)
        .contentShape(Rectangle())
        .animation(.spring(response: 0.35, dampingFraction: 0.8), value: viewModel.activeConfirmation?.id)
        .animation(.spring(response: 0.35, dampingFraction: 0.8), value: viewModel.currentTask?.status)
    }

    // MARK: - Subviews

    @ViewBuilder
    private var headerSection: some View {
        HStack {
            HStack(spacing: 8) {
                Image(systemName: "sparkles")
                    .foregroundColor(.cyan)
                    .font(.headline)
                Text("Actra HUD")
                    .font(.headline)
                    .fontWeight(.bold)
            }

            Spacer()

            Button(action: {
                viewModel.reconnect()
            }) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(viewModel.isConnected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(viewModel.isConnected ? "Live" : "Offline")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.white.opacity(0.1))
                .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .help("Click to reconnect to Actra agent")

            Button(action: {
                NSApplication.shared.terminate(nil)
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.body)
                    .foregroundColor(.secondary.opacity(0.8))
            }
            .buttonStyle(.plain)
            .help("Close Actra HUD")
        }
    }

    @ViewBuilder
    private var alertSection: some View {
        if let alert = viewModel.activeAlert {
            GlassCard {
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.yellow)
                        .font(.title3)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(alert.title)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Text(alert.message)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    Button(action: { viewModel.dismissAlert() }) {
                        Image(systemName: "xmark")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    @ViewBuilder
    private var contentSection: some View {
        if let conf = viewModel.activeConfirmation {
            ConfirmationView(
                request: conf,
                onApprove: { viewModel.approveConfirmation() },
                onDeny: { viewModel.denyConfirmation() }
            )
            .transition(.scale.combined(with: .opacity))
        } else if let task = viewModel.currentTask {
            activeTaskCard(task: task)
        } else {
            idleCard
        }
    }

    @ViewBuilder
    private func activeTaskCard(task: TaskUpdateMessage) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("ACTIVE TASK")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(.secondary)

                    Spacer()

                    Text(task.status)
                        .font(.caption2)
                        .fontWeight(.bold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(statusColor.opacity(0.2))
                        .foregroundColor(statusColor)
                        .clipShape(Capsule())
                }

                Text(task.goal)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .lineLimit(3)

                if !task.step_description.isEmpty {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.triangle.turn.up.right.diamond.fill")
                            .font(.caption2)
                            .foregroundColor(.cyan)
                        Text(task.step_description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                }

                if let reason = task.block_reason, task.status == "BLOCKED" {
                    Text("Blocked: \(reason)")
                        .font(.caption2)
                        .fontWeight(.semibold)
                        .foregroundColor(.orange)
                }

                if task.status == "EXECUTING" || task.status == "PLANNING" || task.status == "VERIFYING" {
                    ProgressView()
                        .progressViewStyle(.linear)
                        .tint(statusColor)
                }
            }
        }
    }

    @ViewBuilder
    private var idleCard: some View {
        GlassCard {
            VStack(spacing: 12) {
                HStack {
                    Image(systemName: "macwindow.badge.plus")
                        .font(.title2)
                        .foregroundColor(.cyan)
                    Text("Ready for Instructions")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Spacer()
                }

                HStack {
                    TextField("Enter goal or task...", text: $goalInput)
                        .textFieldStyle(.plain)
                        .padding(8)
                        .background(Color.black.opacity(0.25))
                        .cornerRadius(8)
                        .onSubmit {
                            submitCurrentGoal()
                        }

                    Button(action: {
                        submitCurrentGoal()
                    }) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title2)
                            .foregroundColor(goalInput.isEmpty ? .secondary : .cyan)
                    }
                    .buttonStyle(.plain)
                    .disabled(goalInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                Divider()

                Button(action: {
                    viewModel.triggerTestConfirmation()
                }) {
                    HStack {
                        Image(systemName: "hand.raised.shield.fill")
                            .font(.caption)
                            .foregroundColor(.orange)
                        Text("Test Safety Confirmation Modal")
                            .font(.caption)
                        Spacer()
                    }
                    .padding(8)
                    .background(Color.white.opacity(0.06))
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
        }
    }

    @ViewBuilder
    private var footerSection: some View {
        GlassCard {
            HealthView(health: viewModel.health)
        }
    }

    private func submitCurrentGoal() {
        let trimmed = goalInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        viewModel.submitGoal(trimmed)
        goalInput = ""
    }
}
