

from exceptions import FPTaylorFormError, FPTaylorRuntimeError
from fpcore_logging import Logger
from fptaylor_form import FPTaylorForm
from fptaylor_lexer import FPTaylorLexer
from fptaylor_parser import FPTaylorParser

import shlex
import subprocess
import tempfile


logger = Logger(level=Logger.MEDIUM, color=Logger.blue)


class FPTaylorResult:
    # Default configuration for FPTaylor when being used for finding FPTaylor
    # forms
    ERROR_FORM_CONFIG = {
        "--abs-error": "false",
        "--find-bounds": "false",
        "--fp-power2-model": "false",
        "--fail-on-exception": "false",
        "--unique-indices": "true",
    }

    # Default configuration for FPTaylor when being used to check answers given
    # by FPTuner. Try for the best answer possible.
    CHECK_CONFIG = {
        "--abs-error": "true",
        "--fp-power2-model": "true",
        "--opt": "gelpia",
        "--opt-exact": "true",
        "--opt-f-rel-tol": "0",
        "--opt-f-abs-tol": "0",
        "--opt-x-rel-tol": "0",
        "--opt-x-abs-tol": "0",
        "--opt-max-iters": "0",
        "--opt-timeout": "0",
    }

    def __init__(self, query, config=None):
        logger.log("FPTaylor query:\n{}", query)
        self.query = query
        self.config = config or FPTaylorResult.ERROR_FORM_CONFIG
        self._run()
        self._extract_fptaylor_forms()

    def _run(self):
        # Open a tempfile we can hand to FPTaylor.
        # The file will be removed upon exiting the with block
        with tempfile.NamedTemporaryFile("w") as f:

            # Write out the query and make sure it is filled
            f.write(self.query)
            f.flush()

            # Put together FPTaylor command
            flags = " ".join([k+" "+v for k, v in self.config.items()])
            command = "fptaylor {} {}".format(flags, f.name)
            logger.llog(Logger.HIGH, "command: {}", command)

            # Call FPTaylor
            # todo: catch when fptaylor is not in the env
            with subprocess.Popen(shlex.split(command),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE) as p:

                # Make sure that the run is complete and grab output
                # todo: should there be a timeout?
                raw_out, raw_err = p.communicate()
                self.out = raw_out.decode("utf8")
                self.err = raw_err.decode("utf8")
                self.retcode = p.returncode


                # If anything went wrong in the call unceremoniusly exit
                if self.retcode != 0:
                    raise FPTaylorRuntimeError(self.query,
                                               command,
                                               self.out,
                                               self.err,
                                               self.retcode)

                # Warn when FPTaylor compains about infinity and domain errors
                # todo: handle when this occurs
                logger.llog(Logger.HIGH, "out:\n{}", self.out.strip())
                if len(self.err) != 0:
                    logger.warning("FPTaylor printed to stderr:\n{}", self.err)

    def _extract_fptaylor_forms(self):
        # Since FPTaylor forms are listed seperate from their corresponding
        # original expressions we will capture both and realign them after
        fptaylor_forms = list()
        original_exprs = list()

        # Get the expression parser ready
        lexer = FPTaylorLexer()
        parser = FPTaylorParser()

        # todo: fix hacky state parser
        state = "find fptaylor forms"
        for line in self.out.splitlines():
            line = line.strip()
            items = line.split()

            if state == "find fptaylor forms":
                # Look for the start of the fptaylor forms
                if len(items) > 0 and line.split()[0] == "v0":
                    state = "capture fptaylor forms"
                continue

            if state == "capture fptaylor forms":
                # Grab fptaylor forms and look for the end of fptaylor forms
                if len(items) > 0 and line.split()[0] == "-1":
                    continue
                if line == "":
                    state = "find original expr"
                    continue
                # Match on:
                #   <int> (<int>): exp = <int>: <expr>
                # Get out the exp = <int> and <expr> parts
                exp = items[4].replace(":", "")
                raw = " ".join(items[5:])
                form = FPTaylorForm(exp, raw)
                fptaylor_forms.append(form)
                continue

            if state == "find original expr":
                # Look for the start of original subexpressions
                if line == "Corresponding original subexpressions:":
                    state = "capture original exprs"
                continue

            if state == "capture original exprs":
                # Grab original subexpressions and look for their end
                if line == "":
                    break
                # Match on:
                #   <int>: <expr>
                # Get out expr
                raw = " ".join(items[1:])
                tokens = lexer.tokenize(raw)
                expr = parser.parse(tokens)
                original_exprs.append(expr)
                continue

            # todo: grab absolute error

        # Catch if the two lists have different lengths
        if len(fptaylor_forms) != len(original_exprs):
            raise FPTaylorFormError(self.out, fptaylor_forms, original_exprs)

        # Set member as list, since zip objects don't play nice
        self.fptaylor_forms = list(zip(original_exprs, fptaylor_forms))
