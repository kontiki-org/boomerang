"""Official Starter Kit entry point (make start) — no AI tool dependency."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / ".engineering" / "ENTRY_PROMPT.txt"


def main():
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    print("Boomerang AI Connector Starter Kit")
    print()
    print("Copy the following message and send it to your AI assistant:")
    print()
    print("----------------------------------------")
    print(prompt)
    print("----------------------------------------")
    print()
    print("Your assistant should read AGENTS.md and follow .engineering/.")


if __name__ == "__main__":
    main()
