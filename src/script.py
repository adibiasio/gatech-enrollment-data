import sys, math

from client import compile_csv


def parse_args(args):
    # default args
    nterms = 4
    subject = None
    filepath = ""
    lower = 0
    upper = math.inf
    include_summer = True

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
            subject = args[i + 1]
            i += 2
        elif args[i] == "-p" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif args[i] == "-m":
            include_summer = False
            i += 1
        elif args[i] == "-l" and i + 1 < len(args):
            try:
                lower = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"Error: {args[i + 1]} is not a valid integer.")
                sys.exit(1)
        elif args[i] == "-u" and i + 1 < len(args):
            try:
                upper = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"Error: {args[i + 1]} is not a valid integer.")
                sys.exit(1)
        else:
            print(f"Unknown or incomplete argument: {args[i]}")
            sys.exit(1)

    return nterms, subject, filepath, lower, upper, include_summer


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Usage: python app.py [-t <num_terms>] [-s <subject>] [-l <lower_bound>] [-u <upper_bound>] [-p <filepath>] [-m]")
        sys.exit(1)

    nterms, subject, filepath, lower, upper, include_summer = parse_args(sys.argv)
    compile_csv(nterms=nterms, subject=subject, lower=lower, upper=upper, include_summer=include_summer, path=filepath, use_ray=True)

