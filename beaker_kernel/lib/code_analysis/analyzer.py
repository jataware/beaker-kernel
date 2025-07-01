import asyncio
from collections import defaultdict
from typing import Optional
from tree_sitter import Language, Tree

from .analysis_types import AnalysisAnnotation, AnalysisAnnotations, AnalysisCategory, AnalysisCodeCells, AnalysisCodeCellLine
from .rules import AnalysisRule
from .analysis_agent import AnalysisResult

class AnalysisEngine:
    # rules: list[TrustRule | AnalysisCategory]
    rules: dict[str, AnalysisRule | AnalysisCategory]
    language: Language
    ast_tree: Optional[Tree]
    _artifact_cache: dict

    def __init__(
            self,
            rules: Optional[list[AnalysisRule | AnalysisCategory]] = None,
            language: Optional[Language] = None,  # TODO: Should this just be subkernel with parser optionally defined there?
        ):
        super().__init__()
        self._artifact_cache = {}
        self.language = language
        self.ast_tree = None
        self.rules = {}
        if rules:
            self.set_rules(rules)

    def set_rules(self, rules: list[AnalysisRule | AnalysisCategory]):
        self.rules.clear()
        for rule in rules:
            # if isinstance(rule, AnalysisCategory):
                # rule = TrustCategoryRule(annotation_type=rule)
            self.add_rule(rule)

    def add_rule(self, rule: AnalysisRule | AnalysisCategory):
        self.rules[rule.id] = rule

    @property
    def mapped_rules(self) -> dict[type[AnalysisRule], list[AnalysisRule]]:
        rule_map  = defaultdict(list)
        for rule in self.rules.values():
            rule_map[rule.__class__].append(rule)
        return rule_map


    async def analyze(self, cells: AnalysisCodeCells) -> AnalysisAnnotations:
        futures = []
        for rule_cls, rules in self.mapped_rules.items():
            data = rule_cls.preprocess_cells(cells, analyzer=self)
            futures.append(
                rule_cls.analyze(cells, data, rules, self)
            )
        results = await asyncio.gather(*futures)

        # Flatten results into a simple list of annotations
        raw_annotations = [
            annotation for result in results
            for annotation in result
        ]

        # cell_annotation_map: dict[str, list[AnalysisCodeCellLine]] = defaultdict(list)
        # raw_annotation: AnalysisResult
        # for raw_annotation in raw_annotations:
        #     rule = self.rules.get(raw_annotation.rule_id, None)
        #     annotation = AnalysisAnnotation(
        #         analysis_category_id="foo",
        #         analysis_item_id="bar",
        #         start=raw_annotation.get


        #     )
        #     # cell_annotation_map[annotation[]]

        return raw_annotations

    async def analyze_iter(self, cells: AnalysisCodeCells):
        futures = []
        for rule_cls, rules in self.mapped_rules.items():
            data = rule_cls.preprocess_cells(cells, analyzer=self)
            futures.append(
                rule_cls.analyze(cells, data, rules, self)
            )
        for future in asyncio.as_completed(futures):
            result = await future
            yield result
