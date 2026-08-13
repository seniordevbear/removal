import argparse
import os
from pathlib import Path

from __face_removal import face_removal


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one PimEyes face-removal workflow test (login -> search -> PROtect)."
    )
    parser.add_argument("--user-id", type=int, default=999999, help="User ID for test context.")
    parser.add_argument("--req-id", type=int, default=1, help="Request ID for test context.")
    parser.add_argument("--email", required=True, help="User email associated with this face removal.")
    parser.add_argument(
        "--face-filename",
        required=True,
        help="Filename from users.url (not full path). Used with PD_FACE_IMAGE_BASE_URL.",
    )
    parser.add_argument(
        "--run-mode",
        default="non-headless",
        choices=["non-headless", "headless"],
        help="Run browser visibly (recommended) or headless.",
    )
    return parser.parse_args()


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    load_env_file(project_dir / ".env")
    args = parse_args()

    screenshot_path = face_removal(
        sio=False,
        target_domain="pimeyescom",
        req_id=args.req_id,
        user_id=args.user_id,
        user_email=args.email,
        face_filename=args.face_filename,
        run_mode=args.run_mode,
    )
    print(f"Test finished. Screenshot: {screenshot_path}")


if __name__ == "__main__":
    main()
