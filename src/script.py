import math, re, sys, time

from loader import Loader
from logger import setup_logger


logger = setup_logger(name="script-runner")


def parse_args(args: list[str]) -> tuple[any]:
    """
    Parses list of command line arguments.

    Args:
        args (list[str]): arguments from sys.argv

    Returns:
        tuple[any]: Parsed arguments with correct types.
    """
    # default args
    nterms = 1
    subjects = set()
    filepath = ""
    ranges = [(0, math.inf)]
    include_summer = True
    one_file = False
    save_all = True
    save_grouped = False

    i = 1
    while i < len(args):
        if args[i] == "-t" and i + 1 < len(args):
            try:
                nterms = int(args[i + 1])
                i += 2
            except ValueError:
                logger.error(f"Error: {args[i + 1]} is not a valid integer.")
                sys.exit(1)
        elif args[i] == "-s" and i + 1 < len(args):
            i += 1
            while i < len(args) and not args[i].startswith("-"):
                subjects.add(args[i].upper())
                i += 1
        elif args[i] == "-p" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif args[i] == "-m":
            include_summer = False
            i += 1
        elif args[i] == "-o":
            one_file = True
            i += 1
        elif args[i] == "-g":
            save_grouped = True
            save_all = False
            i += 1
        elif args[i] == "-a":
            i += 1
        elif args[i] == "-r" and i + 1 < len(args):
            ranges.clear()
            pattern = r'^(\d+)-(\d+)$'
            while i + 1 < len(args) and args[i + 1][0] != '-':
                match = re.match(pattern, args[i + 1])
                if match:
                    ranges.append((int(match.group(1)), int(match.group(2))))
                    i += 1
                else:
                    logger.error(f"Error: {args[i + 1]} is not in the proper format <int>-<int>.")
                    sys.exit(1)
            i += 1
        else:
            logger.error(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    if "-a" in args:
        save_all = True

    return nterms, subjects, filepath, ranges, include_summer, one_file, save_all, save_grouped


def run(argv: list[str]):
    """
    Creates the requested csv.

    Args:
        argv (list[str]): sys.argv cli argument list.
    """
    nterms, subjects, filepath, ranges, include_summer, one_file, save_all, save_grouped = parse_args(argv)
    loader = Loader()
    loader.compile_csv(
        nterms=nterms,
        subjects=subjects,
        ranges=ranges, 
        include_summer=include_summer, 
        one_file=one_file, 
        save_all=save_all,
        save_grouped=save_grouped,
        path=filepath, 
    )


if __name__ == '__main__':
    if len(sys.argv) < 1:
        logger.critical("Usage: python script.py [-t <num_terms>] [-s <subject 1> ... <subject n>] [-r <lower>-<upper> ... <lower>-<upper>] [-p <filepath>] [-m] [-o] [-g] [-a]")
        sys.exit(1)

    start = time.time()
    run(sys.argv)
    logger.debug('ran in ', time.time() - start, ' seconds!')
