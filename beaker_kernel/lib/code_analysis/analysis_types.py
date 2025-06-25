from dataclasses import dataclass
from typing import TypeAlias, Optional, Literal, TypeVar, Generic, Callable, TypedDict, overload

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
        for line_num, line_content in enumerate(self.content.splitlines(keepends=True), start=0):
            line_len = len(line_content)
            line_list.append(AnalysisCodeCellLine(
                cell_id=self.cell_id,
                start_pos=offset,
                end_pos=offset + line_len,
                line_num=line_num,
                content=line_content,
            ))
            offset += line_len
        self._lines = line_list
        return line_list


class AnalysisCodeCells(list[AnalysisCodeCell]):
    _line_ref: dict[tuple[str, int], AnalysisCodeCellLine] = None
    _line_map: dict[int, tuple[int, int]]

    def __init__(self, *args, **kwargs):
        self._line_ref = {}
        self._line_map = {}
        super().__init__(*args, **kwargs)
        offset = 0
        for cell_idx, cell in enumerate(self):
            cell_lines = cell.lines
            for line in cell_lines:
                combined_line_num = line.line_num + offset
                self._line_ref[(cell.cell_id, line.line_num)] = line
                self._line_map[combined_line_num] = (cell_idx, line.line_num)
            offset += len(cell_lines)

    @property
    def lines(self) -> list[dict]:
        line_by_cell = []
        offset = 0
        for cell in self:
            cell_lines = cell.lines
            for line in cell_lines:
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
            "".join((
                f"{line['cell_id']} / {(line['line_num']):{spacing}} : {line['content']}" for line in lines
            ))
        )
        return formatted_code

    @property
    def raw_code(self) -> str:
        return "".join((cell.content for cell in self))

    def unfurl_line(self, line_num: int) -> AnalysisCodeCellLine | None:
        code_cell_idx, code_cell_line = self._line_map.get(line_num, (None, None))
        if code_cell_idx is None:
            return None
        code_cell = self[code_cell_idx]
        line = self._line_ref.get((code_cell.cell_id, code_cell_line), None)
        return code_cell.cell_id, line
