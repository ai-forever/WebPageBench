"""Playwright UI tests for unified bench «Файлы» (bench_files_*)."""

from __future__ import annotations

import re

import pytest

from bench_eval.ui_helpers import (
    event_names,
    files_cabinet_url,
    files_collection_url,
    goto_files_via_hub,
    page_url,
    wait_event,
    wait_files_ready,
)

pytestmark = pytest.mark.ui

COLLECTION_LABELS = (
    "Отчёты лаборатории",
    "Архив проектов",
    "Руководства",
    "Наборы данных",
)


class TestFilesPagesLoad:
    def test_cabinet_lists_collections(self, page, files_track):
        page.goto(files_cabinet_url(files_track), wait_until="networkidle")
        wait_files_ready(page)
        nav = page.locator(".bench-files .collection-nav, .bench-files__nav")
        nav.wait_for(state="visible")
        for label in COLLECTION_LABELS:
            assert page.get_by_role("button", name=label).count() >= 1
        assert "bench_files_cabinet" in page.url
        assert "state_files_main" in page.url

    def test_collection_empty_year_state(self, page, files_track):
        page.goto(
            files_collection_url(files_track, "lab_reports"),
            wait_until="networkidle",
        )
        wait_files_ready(page)
        page.locator(".bench-files__empty").wait_for(state="visible")
        assert "Выберите год" in page.locator(".bench-files__empty").inner_text()
        assert page.locator(".bench-files__card").count() == 0

    def test_select_year_shows_download(self, page, files_track):
        page.goto(files_cabinet_url(files_track), wait_until="networkidle")
        wait_files_ready(page)
        page.get_by_role("button", name="Отчёты лаборатории").click()
        page.wait_for_url(re.compile(r"bench_files_collection"), timeout=15000)
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2024")
        cards = page.locator(".bench-files__card")
        cards.first.wait_for(state="visible")
        assert cards.count() == 2
        card = cards.filter(has_text="lab-reports-2024.pdf")
        assert card.count() == 1
        card_text = card.inner_text()
        assert "Локальный файл" not in card_text
        assert re.search(r"Добавлен \d{2}\.\d{2}\.2024", card_text)
        link = card.get_by_role("link", name="Скачать локальный файл")
        assert link.count() >= 1
        assert "/mocks/files/lab-reports-2024.pdf" in (link.first.get_attribute("href") or "")

    def test_archive_year_lists_monthly_files(self, page, files_track):
        page.goto(files_cabinet_url(files_track), wait_until="networkidle")
        wait_files_ready(page)
        page.get_by_role("button", name="Архив проектов").click()
        page.wait_for_url(re.compile(r"bench_files_collection"), timeout=15000)
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2023")
        cards = page.locator(".bench-files__card")
        cards.first.wait_for(state="visible")
        assert cards.count() >= 12
        text = page.locator(".bench-files").inner_text()
        assert "project-archive-2023.pdf" in text
        assert "2023-01" in text
        assert "2023-06" in text
        june = cards.filter(has_text="project-archive-2023-06.pdf")
        assert re.search(r"Добавлен \d{2}\.06\.2023", june.inner_text())
        dated = cards.filter(has_text="project-archive-2023.pdf")
        assert "Локальный файл" not in dated.inner_text()
        assert re.search(r"Добавлен \d{2}\.\d{2}\.2023", dated.inner_text())

    def test_year_file_counts_differ_across_collections(self, page, files_track):
        page.goto(
            files_collection_url(files_track, "lab_reports"),
            wait_until="networkidle",
        )
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2024")
        page.locator(".bench-files__card").first.wait_for(state="visible")
        lab_count = page.locator(".bench-files__card").count()

        page.goto(
            files_collection_url(files_track, "manuals"),
            wait_until="networkidle",
        )
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2026")
        page.locator(".bench-files__card").first.wait_for(state="visible")
        manuals_count = page.locator(".bench-files__card").count()
        assert lab_count == 2
        assert manuals_count == 3
        assert lab_count != manuals_count


class TestFilesHubNavigation:
    def test_hub_card_opens_cabinet(self, page, files_track):
        page.goto(page_url(files_track, "state_hub", "bench_hub"), wait_until="networkidle")
        page.locator(".bench-hub__card").filter(has_text="Файлы").first.click()
        page.wait_for_url(re.compile(r"bench_files_cabinet"), timeout=15000)
        wait_files_ready(page)
        assert page.locator(".bench-top-nav__link--active").filter(has_text="Файлы").count() == 1

    def test_top_nav_opens_cabinet(self, page, files_track):
        goto_files_via_hub(page, files_track)
        assert page.locator(".bench-files").count() >= 1
        assert page.locator(".bench-top-nav__link--active").filter(has_text="Файлы").count() == 1


class TestFilesEventsAndDownload:
    def test_select_collection_logs_event(self, page, files_track):
        page.goto(files_cabinet_url(files_track), wait_until="networkidle")
        wait_files_ready(page)
        page.get_by_role("button", name="Отчёты лаборатории").click()
        wait_event(files_track, "bench_files_select_collection")
        assert "bench_files_select_collection" in event_names(files_track)

    def test_download_saves_local_pdf(self, page, files_track):
        page.goto(files_cabinet_url(files_track), wait_until="networkidle")
        wait_files_ready(page)
        page.get_by_role("button", name="Отчёты лаборатории").click()
        page.wait_for_url(re.compile(r"bench_files_collection"), timeout=15000)
        wait_files_ready(page)
        page.locator(".bench-files select").first.select_option("2024")
        card = page.locator(".bench-files__card").filter(has_text="lab-reports-2024.pdf")
        link = card.get_by_role("link", name="Скачать локальный файл")
        link.first.wait_for(state="visible")
        with page.expect_download(timeout=15000) as dl_info:
            link.first.click()
        download = dl_info.value
        assert download.suggested_filename
        wait_event(files_track, "bench_files_download")
        assert "bench_files_download" in event_names(files_track)

