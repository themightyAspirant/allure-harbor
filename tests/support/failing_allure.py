import sys


def main() -> None:
    if "--version" in sys.argv:
        print("2.32.0-fake")
        return
    print("generation exploded", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
