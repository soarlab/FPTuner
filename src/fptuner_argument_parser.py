

from fpcore_logging import Logger

import argparse


logger = Logger(level=Logger.MEDIUM, color=Logger.magenta)


def parse_args(argv):
    arg_parser = argparse.ArgumentParser(description="Floating point selector")
    arg_parser.add_argument("query_files",
                            type=str,
                            nargs="+",
                            help="Files containing the target FPCore(s)")
    arg_parser.add_argument("-e", "--error",
                            required=True,
                            type=float,
                            help="The error bound to stay under.")
    arg_parser.add_argument("-v", "--verbosity",
                            nargs="?",
                            default="low",
                            const="medium",
                            choices=list(Logger.CONSTANT_DICT),
                            help="Set output verbosity")
    arg_parser.add_argument("-l", "--log-file",
                            nargs="?",
                            type=str,
                            help="Redirect logging to given file.")
    arg_parser.add_argument("-b", "--bit-widths",
                            nargs="+",
                            choices=["fp32", "fp64", "fp128"],
                            default=["fp32", "fp64"],
                            help="Bit widths to search over")

    args = arg_parser.parse_args(argv[1:])

    logger.set_log_level(Logger.str_to_level(args.verbosity))

    if args.log_file is not None:
        Logger.set_log_filename(args.log_file)

    bws = list(set(args.bit_widths))
    args.bit_widths = sorted(bws, key=lambda s: int(s[2:]))

    logger("Argument settings:")
    logger("  query_files: {}", args.query_files)
    logger("        error: {}", args.error)
    logger("    verbosity: {}", args.verbosity)
    logger("     log_file: {}", args.log_file)
    logger("   bit_widths: {}", args.bit_widths)

    return args
