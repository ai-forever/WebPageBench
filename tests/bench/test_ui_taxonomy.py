"""Playwright tests for each UI interaction class from docs/UI_TAXONOMY.md."""

from __future__ import annotations

import pytest

from ui_taxonomy_cases import UI_TAXONOMY_CASES, cases_by_class
from bench_eval.ui_taxonomy_registry import UI_TAXONOMY_CLASS_IDS, UI_TAXONOMY_CLASSES

pytestmark = pytest.mark.ui


class TestTaxonomyRegistry:
    """Sanity: registry mirrors UI_TAXONOMY.md §2 class IDs."""

    def test_all_taxonomy_classes_registered(self):
        assert len(UI_TAXONOMY_CLASSES) == 19
        assert UI_TAXONOMY_CLASS_IDS == (
            "NAV", "BTN", "TXT", "SEARCH", "SELECT_AC", "SELECT_LIST", "DATE",
            "COUNTER", "CHECK", "RADIO", "CARD", "SEAT", "BASKET", "FAV",
            "FILTER", "AUTH", "PAY", "FILES", "PASSIVE",
        )

    def test_case_matrix_covers_all_classes(self):
        grouped = cases_by_class()
        assert set(grouped) == set(UI_TAXONOMY_CLASS_IDS)
        for class_id in UI_TAXONOMY_CLASS_IDS:
            assert len(grouped[class_id]) >= 8, f"{class_id} has only {len(grouped[class_id])} cases"

    def test_case_matrix_size_near_200(self):
        assert len(UI_TAXONOMY_CASES) >= 150


@pytest.mark.parametrize(
    "case",
    UI_TAXONOMY_CASES,
    ids=[c.case_id for c in UI_TAXONOMY_CASES],
)
class TestTaxonomyUI:
    """Parametrized UI interaction tests (~160 cases)."""

    def test_ui_taxonomy_case(self, page, taxonomy_track: str, case):
        case.run(page, taxonomy_track)
        case.verify(taxonomy_track)
