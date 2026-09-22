"""Actra CLI entry point."""

from __future__ import annotations

import argparse
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from actra.config import Settings
from actra.mac.permissions import check_all_permissions, print_permission_guide


def _print_banner() -> None:
    print(textwrap.dedent("""\
    ╔══════════════════════════════════════════════╗
    ║   Actra — macOS Computer-Use AI Agent        ║
    ║   Phase 1: Laptop-only Prototype             ║
    ╚══════════════════════════════════════════════╝
    """))


def _check_permissions() -> bool:
    """Check macOS permissions and warn if missing."""
    perms = check_all_permissions()
    missing = [k for k, v in perms.items() if not v]
    if missing:
        print(f"⚠️  Missing permissions: {', '.join(missing)}")
        print_permission_guide()
        print()
        # Don't block — some tools work without full permissions
    return len(missing) == 0


def _run_interactive(agent) -> None:
    """Interactive REPL loop."""
    print("Interactive mode. Type your goal, or 'quit' to exit.\n")
    while True:
        try:
            goal = input("🎯 Goal: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not goal:
            continue
        if goal.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        task = agent.run(goal)
        print()

        if task.context.get("final_message"):
            print(f"📝 {task.context['final_message']}")
        print(f"Status: {task.status.value}")
        print(f"Steps executed: {task.step_index}")
        print()


def main() -> None:
    """Main entry point for the actra CLI."""
    parser = argparse.ArgumentParser(
        prog="actra",
        description="Actra — macOS computer-use AI agent",
    )
    parser.add_argument(
        "goal",
        nargs="?",
        help='Natural-language goal (e.g., "Open Safari and search for iQOO 15")',
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive REPL mode",
    )
    parser.add_argument(
        "--hud",
        action="store_true",
        help="Launch the Native SwiftUI HUD overlay and run in background service mode",
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as a background daemon service listening for HUD commands",
    )
    parser.add_argument(
        "--no-confirm",
        nargs="?",
        const="sensitive",
        default=None,
        choices=["sensitive", "all", "none"],
        help="Bypass confirmation prompts: 'sensitive' (default if flag given) bypasses SENSITIVE tier; 'all' bypasses SENSITIVE and DANGEROUS tiers",
    )
    parser.add_argument(
        "--skip-permission-check",
        action="store_true",
        help="Skip macOS permission checks on startup",
    )

    args = parser.parse_args()

    _print_banner()

    # Load settings
    settings = Settings.load()

    # Check permissions
    if not args.skip_permission_check:
        _check_permissions()

    # Override confirmation if requested on CLI
    if args.no_confirm is not None:
        no_confirm_mode = args.no_confirm
        settings = Settings(
            ollama_host=settings.ollama_host,
            model_name=settings.model_name,
            num_ctx=settings.num_ctx,
            max_retries=settings.max_retries,
            require_confirmation=(no_confirm_mode != "all"),
            no_confirm=no_confirm_mode,
            log_level=settings.log_level,
            log_dir=settings.log_dir,
            screenshot_dir=settings.screenshot_dir,
        )

    # Create agent
    try:
        from actra.agent import ActraAgent
        agent = ActraAgent(settings=settings)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    # Auto-launch Swift HUD if requested
    hud_proc = None
    if args.hud:
        hud_dir = Path(__file__).resolve().parents[2] / "actra-hud"
        hud_bin = hud_dir / ".build" / "debug" / "ActraHUD"
        if not hud_bin.exists():
            print("📦 Building ActraHUD...")
            subprocess.run(["swift", "build"], cwd=str(hud_dir), check=False)
        if hud_bin.exists():
            print("🚀 Launching Native Actra HUD...")
            hud_proc = subprocess.Popen([str(hud_bin)])
        else:
            print("⚠️ ActraHUD binary not found. Build it with: cd actra-hud && swift build")

    try:
        # Run mode
        if args.daemon:
            print("🤖 Actra daemon running. Waiting for commands from HUD (Ctrl+C to quit)...")
            try:
                while True:
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                print("\nShutting down Actra daemon...")
        elif args.goal is not None:
            task = agent.run(args.goal)
            if task.context.get("final_message"):
                print(f"\n📝 {task.context['final_message']}")
            print(f"\n✨ Status: {task.status.value} | Steps: {task.step_index}")
        else:
            _run_interactive(agent)
    finally:
        if hud_proc and hud_proc.poll() is None:
            hud_proc.terminate()


if __name__ == "__main__":
    main()
