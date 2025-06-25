import codecs
import dill
from abc import ABC, abstractmethod
from tree_sitter import Tree, Node, Parser, Language
from typing import TypeVar, Callable, Optional, TYPE_CHECKING

from ..analysis_agent import AnalysisResult
from ..analysis_types import AnalysisCodeCells, AnalysisCategory, AnalysisItem

if TYPE_CHECKING:
    from ..analyzer import CodeAnalyzer

InternalRepr = TypeVar("InternalRepr")

class TrustRule(ABC):
    id: str

    def __init__(self, id):
        self.id = id

    @classmethod
    @abstractmethod
    async def check(cls, cells: AnalysisCodeCells, data: InternalRepr, rules: "list[TrustRule]", analyzer: "CodeAnalyzer") -> list[AnalysisResult]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def preprocess_cells(cls, cells: AnalysisCodeCells,  analyzer: "CodeAnalyzer") -> InternalRepr:
        raise NotImplementedError()


class ASTRule(TrustRule):
    filter: Callable

    def __init__(self, id: str, filter: Callable):
        super().__init__(id)
        self.filter = filter

    @classmethod
    async def check(cls, cells: AnalysisCodeCells, data: Tree, rules: "list[ASTRule]", analyzer: "CodeAnalyzer") -> list[AnalysisResult]:
        matches = []
        for rule in rules:
            print(f"Checking {rule.__class__.__name__} '{rule.id}'")
            matches.extend(rule.filter(cells, data, analyzer, rule))
        return matches

    @classmethod
    def preprocess_cells(cls, cells: AnalysisCodeCells, analyzer) -> Tree:
        code = cells.raw_code
        if not isinstance(code, bytes):
            code = code.encode()
        parser = Parser(analyzer.language)
        tree = parser.parse(code)
        return tree


class LLMRule(TrustRule):
    rule_prompt: Optional[str]

    def __init__(self, id: str, prompt: Optional[str]):
        super().__init__(id)
        self.rule_prompt = prompt

    @property
    def query(self) -> str:
        query = f"""\
id: `{self.id}`
instructions:
```
{self.rule_prompt.strip()}
```
"""
        return query

    @classmethod
    async def check(cls, cells: AnalysisCodeCells, data: str, rules: "list[LLMRule]", analyzer: "CodeAnalyzer") -> list[AnalysisResult]:
        from ..analysis_agent import AnalysisResult, CodeAnalysisAgent
        from ...config import config
        model = config.get_model()
        agent = CodeAnalysisAgent(
            model=model,
 )
        agent.add_context(f"""\
Code to run rules against:
```
{data}
```
""")
        formatted_rules = [rule.query for rule in rules]
        joined_rules = "\n====\n".join(formatted_rules)
        result = await agent.react_async(query=joined_rules)
        try:
            result = result.encode()
            result = codecs.decode(result, 'base64')
        except:
            pass
        try:
            # Attempt to unpickle/undill the result.
            result = dill.loads(result)
        except dill.UnpicklingError:
            # Allow result to pass through as returned.
            pass
        return result

    @classmethod
    def preprocess_cells(cls, cells, analyzer) -> str:
        return cells.formatted_code


class TrustAnnotationTypesLLMRule(LLMRule):
    annotation_type = AnalysisCategory
    def __init__(self, annotation_type: AnalysisCategory):
        super().__init__(id=f"code_analysis_{annotation_type.id}", prompt=None)
        self.annotation_type = annotation_type

    @property
    def query(self) -> str:
        content = []
        content.append(f"""
# {self.annotation_type.display_label} ({self.annotation_type.id})""".strip())
        for annotation in self.annotation_type.analysis_items:
            content.append(
                f"""\
## {annotation.title} ({annotation.id})
    id: {annotation.id}
    severity: {annotation.severity}
    description/instructions: \\
```
{annotation.description}
```"""
            )
        print(content)
        return "\n\n".join(content)





groundings = AnalysisCategory(
    id="grounding",
    display_label="Ungrounded Information",
    color="#D6852C",
    icon="",
    analysis_items=[
        AnalysisItem(
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
        AnalysisItem(
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
        AnalysisItem(
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

assumptions = AnalysisCategory(
    id="assumptions",
    display_label="Assumptions in Code",
    color="#E24609",
    icon="",
    analysis_items=[
        AnalysisItem(
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

#         """
# (
#  (comment)* @comment
#  .
#  (expression_statement
#   (assignment
#     left: (_) @left
#     right: ((_)* @right
#             (#any-of? @right
#                 "string"
#                 "integer"
#                 "float"
#             )
#            )
#   )
#  )
#  .
#  (comment)* @comment
# )
#         """

def literalCheckAstFilter(cells: AnalysisCodeCells, tree: Tree, analyzer: "CodeAnalyzer", rule: ASTRule) -> list[tuple[ASTRule, Node]]:
    language = analyzer.language
    print(f"Checking literal filter against {tree}")
    query = language.query(
        """
(
 (comment)* @comment
 .
 (expression_statement
  (assignment
    left: (_) @left
    right: ([
        (string)
        (integer)
        (float)
    ].) @right
   ) @assignment
 )
 .
 (comment)* @comment
)
        """
    )
    raw_matches = query.matches(tree.root_node)

    results: list[AnalysisResult] = []
    for _, match in raw_matches:
        node: Node = match["right"][0]
        start_line, start_pos = node.start_point
        end_line, end_pos = node.end_point
        cell_id, start_unfurled_line = cells.unfurl_line(start_line)
        end_unfurled_line = start_unfurled_line if end_line == start_line else cells.unfurl_line(node)[1]

        result = AnalysisResult(
            cell_id=cell_id,
            code_start_line=start_unfurled_line.line_num,
            code_end_line=end_unfurled_line.line_num,
            code_start_line_pos=start_pos,
            code_end_line_pos=end_pos,
            rule_id=rule.id,
            issue_type="ast-literal",
            extra_info="No extra info",
        )
        results.append(result)
    return results


# def literalCheckNormalizer(rule, match, cells):
#     pass

# def nodeHighlighterNormalizer(rule, node, cells):
#     pass

LiteralCheckAST = ASTRule(
    id="ast_literal",
    filter=literalCheckAstFilter,
    # normalizer=nodeHighlighterNormalizer,
    # normalizer=literalCheckNormalizer,
)
