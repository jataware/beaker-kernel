from dataclasses import dataclass
from typing import TypeAlias, Optional, Literal, TypeVar, Generic, Callable, TypedDict

from pydantic import BaseModel


class AnalysisItem(BaseModel):
    id: str
    title: str
    description: str
    severity: Literal["major", "minor", "warning", "info", "hint"] = "info"
    link: Optional[str] = None


class AnalysisCategory(BaseModel):
    id: str
    display_label: str
    color: Optional[str] = None
    icon: Optional[str] = None
    analysis_items: list[AnalysisItem]


class AnalysisAnnotation:
    analysis_category_id: str
    analysis_item_id: str
    start: int
    end: int
    title_override: Optional[str]
    message_override: Optional[str]
    message_extra: Optional[str]
AnalysisAnnotations: TypeAlias = list[AnalysisAnnotation]


@dataclass
class AnalysisCodeCellLine:
    cell_id: str
    start_pos: int
    end_pos: int
    line_num: int
    content: str


@dataclass
class AnalysisCodeCell:
    cell_id: str
    notebook_id: str
    content: str
    _lines: Optional[list[AnalysisCodeCellLine]] = None

    @property
    def lines(self) -> list[AnalysisCodeCellLine]:
        if self._lines is not None:
            return self._lines
        offset = 0
        line_list: list[AnalysisCodeCellLine] = []
        for line_num, content in enumerate(self.content.splitlines(), start=1):
            line_len = len(content)
            line_list.append(AnalysisCodeCellLine(
                start_pos=offset,
                end_pos=offset + line_len,
                line_num=line_num,
                content=content,
            ))
            offset += line_len
        self._lines = line_list
        return line_list


class AnalysisCodeCells(list[AnalysisCodeCell]):
    _line_ref: dict[tuple[str, int], AnalysisCodeCellLine] = None

    @property
    def lines(self) -> list[dict]:
        self._line_ref = {}
        line_by_cell = []
        offset = 0
        for cell in self:
            cell_lines = cell.lines
            for line in cell_lines:
                self._line_ref[(cell.cell_id, line.line_num)] = line
                line_by_cell.append({
                    "cell_id": cell.cell_id,
                    "line_num": line.line_num + offset,
                    "content": line.content,
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

    def unfurl_line(self, codecell_id: str, line_num: int) -> AnalysisCodeCellLine | None:
        if self._line_ref is None:
            self.lines  # Prime cache
        line = self._line_ref.get((codecell_id, line_num), None)
        return line
