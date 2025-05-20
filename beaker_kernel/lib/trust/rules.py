from .linter import TrustRule, ASTRule, LLMRule, TrustLinter, TrustAnnotationType, TrustAnnotationMessageType
from tree_sitter import Tree, Node


groundings = TrustAnnotationType(
    id="grounding",
    display_label="Ungrounded Information",
    color="#D6852C",
    icon="",
    message_types=[
        TrustAnnotationMessageType(
            id="ungrounded_value",
            title="Ungrounded Value",
            description="""\
This issue arises when a particular value is used by the LLM Agent, but the value is not grounded.
I.e. it is used without identifying how the value is defined and/or why it was selected.
Obvious examples such as `state = 'TX'`, `timeout = 15` and `year = 2024` should not be annotated, but examples such as
`state = 22` or `param_code = "44201"` should have their values grounded and should be annotated if grounding is not
provided.
            """.strip(),
            severity="warning",
        ),
        TrustAnnotationMessageType(
            id="ungrounded_methodology",
            title="Ungrounded Methodology",
            description="""\
This issue arises when a particular algorithm or methodology is used by the LLM Agent, but the reasoning behind said use
is not grounded. This is particularly important when multiple algorithms or methodologies could be used and a particular
one was chosen.
When generating the annotation message, please provide information on the strengths and weaknesses of the methodology
compared to alternatives.
If there are no other reasonable methodologies or all other methodologies are essentially equivalent, code probably does
not require annotation, as the annotation would not provide any useful, actionable information to the user.
            """.strip(),
            severity="info",
        ),
        TrustAnnotationMessageType(
            id="ungrounded_fact",
            title="Ungrounded Fact",
            description="""\
This issue arises when the agent assumes a factual value without the fact being grounded.
This mostly occurs when the LLM believes that it "knows" a value based on its training, but the value could be based off
of outdated or incorrect information.
            """.strip(),
            severity="minor",
        ),
    ],
)

assumptions = TrustAnnotationType(
    id="assumptions",
    display_label="Assumptions in Code",
    color="#E24609",
    icon="",
    message_types=[
        TrustAnnotationMessageType(
            id="assumption",
            title="Assumption by Agent",
            description="""\
This issue arises when the agent makes assumptions on how to accomplish a request that are not part of the request by
the user and for which reasonable alternatives exist.
            """.strip(),
            severity="warning",
        )
    ],
)


# LiteralCheckLLM = LLMRule(
#     id="llm_literal",
#     prompt="""
# Select any instances where a variable is defined using a hard-coded values not provided by the user.
# This is especially important if the value is an identifier and is presented without being grounded.
#     """
# )


def literalCheckAstFilter(tree: Tree, linter: TrustLinter) -> list[Node]:
    print(f"Checking literal filter against {tree}")
    return []


LiteralCheckAST = ASTRule(
    id="ast_literal",
    filter=literalCheckAstFilter

)
