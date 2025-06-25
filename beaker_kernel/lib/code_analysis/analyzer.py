import asyncio
from collections import defaultdict
from typing import Optional
from tree_sitter import Language, Tree

from .analysis_types import AnalysisAnnotations, AnalysisCategory, AnalysisCodeCells, AnalysisCodeCellLine
from .rules import TrustRule, TrustAnnotationTypesLLMRule

class CodeAnalyzer:
    rules: list[TrustRule | AnalysisCategory]
    language: Language
    ast_tree: Optional[Tree]
    _artifact_cache: dict

    def __init__(
            self,
            rules: Optional[list[TrustRule | AnalysisCategory]] = None,
            language: Optional[Language] = None,  # TODO: Should this just be subkernel with parser optionally defined there?
        ):
        super().__init__()
        self._artifact_cache = {}
        self.language = language
        self.ast_tree = None
        self.rules = []
        if rules:
            self.set_rules(rules)

    def set_rules(self, rules: list[TrustRule | AnalysisCategory]):
        self.rules = []
        for rule in rules:
            if isinstance(rule, AnalysisCategory):
                rule = TrustAnnotationTypesLLMRule(annotation_type=rule)
            self.add_rule(rule)

    def add_rule(self, rule: TrustRule | AnalysisCategory):
        self.rules.append(rule)

    async def analyze(self, cells: AnalysisCodeCells) -> AnalysisAnnotations:
        futures = []
        rule_map: dict[type[TrustRule], list[TrustRule]] = defaultdict(list)
        for rule in self.rules:
            rule_map[rule.__class__].append(rule)
        for rule_cls, rules in rule_map.items():
            data = rule_cls.preprocess_cells(cells, analyzer=self)
            futures.append(
                rule_cls.check(cells, data, rules, self)
            )
        results = await asyncio.gather(*futures)
        annotations = [
            annotation for result in results
            for annotation in result
        ]

        # cell_annotation_map: dict[str, list[AnalysisCodeCellLine]] = defaultdict(list)
        # for annotation in annotations:
            # print(annotation)
            # cell_annotation_map[annotation[]]

        return annotations

# async def check_and_normalize(cls: type[TrustRule], cells, data, rules, analyzer):
    # results = await cls.check(cells=cells, data=data, rules=rules, analyzer=analyzer)
    # return results
    # raw_result = await cls.check(data=data, rules=rules, analyzer=analyzer)
    # normalized_result = cls.normalize_results(cells=cells, results=raw_result, analyzer=analyzer)
    # return normalized_result
