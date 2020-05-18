

from exceptions import GelpiaInfError
from fpcore_logging import Logger
from fractions import Fraction
from math import isinf

import gelpia
import gelpia_logging


logger = Logger(level=Logger.MEDIUM, color=Logger.green)


class GelpiaResult:

    # Setup logging to avoid runtime error
    gelpia_logging.set_log_filename(None)

    # Silence gelpia
    gelpia_logging.set_log_level(-10)

    # Setup gelpia's env
    gelpia.setup_requirements(git_dir=gelpia.GIT_DIR)

    # Setup rust's env
    RUST_EXECUTABLE = gelpia.setup_rust_env(git_dir=gelpia.GIT_DIR,
                                            debug=False)

    # Tell gelpia to always try as hard as possible
    CONFIG = {
        "epsilons": (1e-4, 1e-4, 0),
        "timeout": 10,
        "grace": 0,
        "update": 0,
        "iters": 2**18,
        "seed": 0,
        "debug": False,
        "src_dir": gelpia.SRC_DIR,
        "executable": RUST_EXECUTABLE,
    }

    def __init__(self, inputs, expr):
        # Format inputs, target expression, and set as member
        # todo: this float cast can loose information
        lines = ["{} = [{}, {}];".format(name,
                                         float(Fraction(domain[0].source)),
                                         float(Fraction(domain[1].source)))
                 for name, domain in inputs.items()]
        lines.append(expr.infix_str())
        self.query = "\n".join(lines)
        logger.log("query:\n{}", self.query)

        # Run and set results as member
        self.max_lower, self.max_upper = gelpia.find_max(function=self.query,
                                                         **GelpiaResult.CONFIG)

        if isinf(self.max_upper):
            raise GelpiaInfError(self.query)

        logger.llog(Logger.HIGH, "result = [{}, {}]",
                    self.max_lower, self.max_upper)
