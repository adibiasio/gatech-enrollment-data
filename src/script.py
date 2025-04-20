import math, re, sys

from client import compile_csv


def parse_args(args):
    # default args
    nterms = 1
    subjects = set()
    filepath = ""
    ranges = [(0, math.inf)]
    include_summer = True
    one_file = False

    i = 1
    while i < len(args):
        if args[i] == "-t" and i + 1 < len(args):
            try:
                nterms = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"Error: {args[i + 1]} is not a valid integer.")
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
        elif args[i] == "-r" and i + 1 < len(args):
            ranges.clear()
            pattern = r'^(\d+)-(\d+)$'
            while i + 1 < len(args) and args[i + 1][0] != '-':
                match = re.match(pattern, args[i + 1])
                if match:
                    ranges.append((int(match.group(1)), int(match.group(2))))
                    i += 1
                else:
                    print(f"Error: {args[i + 1]} is not in the proper format <int>-<int>.")
                    sys.exit(1)
            i += 1
        else:
            print(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    return nterms, subjects, filepath, ranges, include_summer, one_file


def run(argv, use_ray=True):
    nterms, subjects, filepath, ranges, include_summer, one_file = parse_args(argv)
    compile_csv(
        nterms=nterms,
        subjects=subjects,
        ranges=ranges, 
        include_summer=include_summer, 
        one_file=one_file, 
        path=filepath, 
        use_ray=use_ray
    )


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python script.py [-t <num_terms>] [-s <subject 1> ... <subject n>] [-r <lower>-<upper> ... <lower>-<upper>] [-p <filepath>] [-m] [-o]")
        sys.exit(1)

    run(sys.argv)

