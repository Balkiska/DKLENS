import argparse
import sys
from cli.scan_command import scan_entry


def main():
    parser = argparse.ArgumentParser(prog="docklens")
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("image")
    scan_parser.add_argument("--no-pull", action="store_true")

    args = parser.parse_args()

    if args.command == "scan":
        try:
            scan_entry(args.image, auto_pull=not args.no_pull)
        except Exception as e:
            print(f"❌ {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
