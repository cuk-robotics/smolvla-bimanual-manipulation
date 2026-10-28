"""Audit Git sharing rules and common secret patterns; never print secret values."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IGNORED = (
    "AGENTS.md", "PROJECT_CONTEXT.md", "GEMINI_TO_CODEX.md", ".codex/config.toml",
    ".agents/session.json", ".claude/settings.local.json", ".mcp.json",
    "configs/local/hardware.json", "calibration/so101/dual_follower_right.json",
    "outputs/right_gripper_direction_20261014_191638_719717/report.json",
    "data/lerobot/session/meta/info.json", "models/model.safetensors",
    "checkpoints/model.pt", "runs/train/config.json", "logs/run.log",
    ".env", ".env.production", ".envrc", "credentials.json", "secrets.json",
    "stored_tokens", "token", "id_ed25519", "secret.pfx", "settings.local.toml",
    "build/lib/cuk_robotics/__init__.py", "dist/package.whl", "package.whl",
    "model.7z", "local_bundle.zip", ".venv/pyvenv.cfg", "src/__pycache__/module.pyc",
    ".pytest_cache/state", "notes.md.bak", "viewer.dmp",
)
EXPECTED_SHARED = (
    "README.md", "docs/operations.md", "docs/recording.md", "docs/inference.md",
    ".gitignore", ".gitattributes", "LICENSE", ".github/workflows/ci.yml",
    "docs/troubleshooting.md", "docs/repository.md", "scripts/run_robot.py",
    "scripts/check_git_hygiene.py", "scripts/windows/operation.bat",
    "src/cuk_robotics/teleoperation/cli.py", "configs/hardware/so101_bimanual.example.json",
    "configs/recording/beverage.json", "tests/test_operation.py",
    "requirements/constraints-windows.txt", "templates/dataset_card.md",
    ".env.example", ".env.production.example", "assets/example.png", "id_ed25519.pub",
)
PATTERNS = {
    "hugging_face_token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "openai_or_anthropic_token": re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "credential_url": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
    "assigned_secret": re.compile(r'''(?im)^\s*[\w.-]*(?:api[_-]?key|access[_-]?token|password|secret)[\w.-]*\s*[:=]\s*["']?[A-Za-z0-9_+/=-]{20,}'''),
}


def git(*args, input=None, allowed=(0,)):
    result = subprocess.run(["git", *args], cwd=ROOT, input=input, capture_output=True)
    if result.returncode not in allowed:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout.decode("utf-8", errors="replace")


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(value for key, value in attrs if key in ("href", "src") and value)


def audit():
    candidates = sorted(set(filter(None, git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0"))))
    tracked_ignored = list(filter(None, git("ls-files", "-z", "-ci", "--exclude-standard").split("\0")))
    samples = (*EXPECTED_IGNORED, *EXPECTED_SHARED)
    matched = set(git("check-ignore", "--no-index", "--stdin", input=("\n".join(samples) + "\n").encode(), allowed=(0, 1)).splitlines())
    classification_errors = [p for p in EXPECTED_IGNORED if p not in matched] + [p for p in EXPECTED_SHARED if p in matched]
    findings, link_errors, skipped, large_files = [], [], [], []
    scanned = 0
    for relative in candidates:
        path = ROOT / relative
        if not path.is_file():
            continue  # Preserve existing deletions; do not restore files.
        size = path.stat().st_size
        if size > 10_000_000:
            large_files.append({"path": relative, "bytes": size})
        if size > 2_000_000:
            skipped.append(relative)
            continue
        raw = path.read_bytes()
        try:
            if b"\0" in raw:
                skipped.append(relative)
                continue
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            skipped.append(relative)
            continue
        scanned += 1
        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                findings.append({"path": relative, "line": content.count("\n", 0, match.start()) + 1, "kind": kind})
        targets = []
        if path.suffix == ".md":
            targets = re.findall(r"\]\(([^)]+)\)", content)
        elif path.suffix == ".html":
            parser = HTMLLinks()
            parser.feed(content)
            targets = parser.targets
        for target in targets:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if not (path.parent / unquote(parsed.path)).exists():
                link_errors.append({"path": relative, "target": target})
    return {
        "head": git("rev-parse", "--short", "HEAD").strip(),
        "existing_text_files_scanned": scanned, "skipped_nontext_or_large_files": skipped,
        "tracked_but_ignored": tracked_ignored, "classification_samples_checked": len(samples),
        "classification_errors": classification_errors, "credential_pattern_findings": findings,
        "document_link_errors": link_errors, "large_publishable_files": large_files,
        "scope": "Current tracked/nonignored working files and common patterns; does not scan past commits or guarantee absence of all secrets.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Optional local JSON report path")
    options = parser.parse_args()
    report = audit()
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if options.report:
        options.report.parent.mkdir(parents=True, exist_ok=True)
        options.report.write_text(serialized, encoding="utf-8")
    print(serialized)
    if any(report[name] for name in ("tracked_but_ignored", "classification_errors", "credential_pattern_findings", "document_link_errors", "large_publishable_files")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
