import asyncio
import codecs
import dill
import tree_sitter_python as tspython
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias, Optional, Literal, TypeVar, Generic, Callable, TypedDict
from tree_sitter import Language, Parser, Tree, Point

from pydantic import BaseModel


class TrustAnnotationMessageType(BaseModel):
    id: str
    title: str
    description: str
    severity: Literal["major", "minor", "warning", "info", "hint"] = "info"
    link: Optional[str] = None


class TrustAnnotationType(BaseModel):
    id: str
    display_label: str
    color: Optional[str] = None
    icon: Optional[str] = None
    message_types: list[TrustAnnotationMessageType]


class TrustAnnotation:
    error_type: str
    error_id: str
    start: int
    end: int
    title_override: Optional[str]
    message_override: Optional[str]
    message_extra: Optional[str]
TrustAnnotations: TypeAlias = list[TrustAnnotation]


@dataclass
class CodeCellLineDict:
    start_point: Point
    end_point: Point
    start_pos: int
    end_pos: int
    line_num: int
    content: str


@dataclass
class CodeCell:
    cell_id: str
    notebook_id: str
    content: str

    @property
    def lines(self) -> list[CodeCellLineDict]:
        offset = 0
        line_list: list[CodeCellLineDict] = []
        for line_num, content in enumerate(self.content.splitlines(), start=1):
            line_len = len(content)
            line_list.append({
                "start_point": Point(line_num-1, 0),
                "end_point": Point(line_num-1, line_len),
                "start_pos": offset,
                "end_pos": offset + line_len,
                "line_num": line_num,
                "content": content,
            })
            offset += line_len
        return line_list


class CodeCells(list[CodeCell]):
    @property
    def lines(self):
        line_by_cell = []
        offset = 0
        for cell in self:
            cell_lines = cell.lines
            for line in cell_lines:
                line_by_cell.append({
                    "cell_id": cell.cell_id,
                    "line_num": line["line_num"] + offset,
                    "content": line["content"],
                })
            offset += len(cell_lines)
        return line_by_cell

    @property
    def formatted_code(self):
        lines = self.lines
        spacing = len(str(len(lines)))
        formatted_code = (
            "# {cell_id} / {line_num} : {content}\n" +
            "\n".join((
            f"{line['cell_id']} / {(line['line_num']):{spacing}} : {line['content']}" for line in lines
            ))
        )
        return formatted_code

    @property
    def raw_code(self) -> str:
        return "\n".join((cell.content for cell in self))

    def unfurl_line(self):
        pass



T = TypeVar("T")

class TrustRule(ABC):
    id: str

    def __init__(self, id):
        self.id = id

    @classmethod
    @abstractmethod
    async def check(cls, data: T, rules: "list[TrustRule]", linter: "TrustLinter"):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def preprocess_cells(cls, cells: CodeCells,  linter: "TrustLinter") -> T:
        raise NotImplementedError()

class ASTRule(TrustRule):
    filter: Callable

    def __init__(self, id: str, filter: Callable):
        super().__init__(id)
        self.filter = filter

    @classmethod
    async def check(cls, data: Tree, rules: "list[ASTRule]", linter: "TrustLinter"):
        for rule in rules:
            print(f"Checking {rule.__class__.__name__} '{rule.id}'")
            return rule.filter(data, linter)

    @classmethod
    def preprocess_cells(cls, cells: CodeCells, linter) -> Tree:
        code = cells.raw_code
        if not isinstance(code, bytes):
            code = code.encode()
        parser = Parser(linter.language)
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
    async def check(cls, data: str, rules: "list[LLMRule]", linter: "TrustLinter"):
        from .trust_agent import AnalysisObject, TrustAgent
        from ..config import config
        model = config.get_model()
        agent = TrustAgent(
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
    def preprocess_cells(cls, cells, linter) -> str:
        return cells.formatted_code


class TrustAnnotationTypesLLMRule(LLMRule):
    annotation_type = TrustAnnotationType
    def __init__(self, annotation_type: TrustAnnotationType):
        super().__init__(id=f"trust_annoations_{annotation_type.id}", prompt=None)
        self.annotation_type = annotation_type

    @property
    def query(self) -> str:
        content = []
        content.append(f"""
# {self.annotation_type.display_label} ({self.annotation_type.id})""".strip())
        for annotation in self.annotation_type.message_types:
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


class TrustLinter:
    rules: list[TrustRule | TrustAnnotationType]
    language: Language
    ast_tree: Optional[Tree]
    _artifact_cache: dict

    def __init__(
            self,
            rules: Optional[list[TrustRule | TrustAnnotationType]] = None,
            language: Optional[Language] = None,  # TODO: Should this just be subkernel with parser optionally defined there?
        ):
        super().__init__()
        self._artifact_cache = {}
        self.language = language
        self.ast_tree = None
        self.rules = []
        if rules:
            self.set_rules(rules)

    def set_rules(self, rules: list[TrustRule | TrustAnnotationType]):
        self.rules = []
        for rule in rules:
            if isinstance(rule, TrustAnnotationType):
                rule = TrustAnnotationTypesLLMRule(annotation_type=rule)
            self.add_rule(rule)

    def add_rule(self, rule: TrustRule | TrustAnnotationType):
        self.rules.append(rule)


    # def lint(self, code: str) -> TrustAnnotations:
    async def lint(self, cells: CodeCells) -> TrustAnnotations:
        futures = []
        rule_map: dict[type[TrustRule], list[TrustRule]] = defaultdict(list)
        for rule in self.rules:
            rule_map[rule.__class__].append(rule)
        for cls, rules in rule_map.items():
            data = cls.preprocess_cells(cells, linter=self)
            futures.append(
                cls.check(data=data, rules=rules, linter=self)
            )
        results = await asyncio.gather(*futures)
        annotations = [
            annotation for result in results
            for annotation in result
        ]
        print(annotations)
        return annotations
