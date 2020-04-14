

from fpcore_lexer import FPCoreLexer

import can_have_fptaylor_form_ast
import equals_ast
import expand_ast
import fpcore_ast
import infix_str_ast
import to_single_assignment_ast


FPCoreLexer.UNARY_OPERATIONS.add("zero_sin")
FPCoreLexer.UNARY_OPERATIONS.add("one_sin")
FPCoreLexer.UNARY_OPERATIONS.add("m_one_sin")
FPCoreLexer.UNARY_OPERATIONS.add("taylor_1_sin")
FPCoreLexer.UNARY_OPERATIONS.add("taylor_3_sin")
