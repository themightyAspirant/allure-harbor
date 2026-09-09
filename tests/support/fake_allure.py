import argparse
import sys
from pathlib import Path


def main() -> None:
    if "--version" in sys.argv:
        print("2.32.0-fake")
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("results", nargs="?")
    parser.add_argument("-o", "--output")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.command != "generate" or not args.output:
        sys.exit(1)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(
        "<html><body>fake-allure</body></html>",
        encoding="utf-8",
    )
    (output / "app.js").write_text("console.log('ok');", encoding="utf-8")


if __name__ == "__main__":
    main()
