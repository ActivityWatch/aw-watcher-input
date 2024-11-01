from aw_watcher_input.main import main as _main
from aw_watcher_input.config import parse_args

def main() -> None:
    args = parse_args()

    # Start watcher
    _main(args, testing=args.testing)

if __name__ == "__main__":
    main()
