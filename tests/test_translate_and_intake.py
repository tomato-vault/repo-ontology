"""Tests for translate and intake functionality."""

from pathlib import Path
import pytest
from repo_ontology.loader import OntologyRegistry
from repo_ontology.models import (
    ViewBinding,
    ViewBindingBackend,
    ViewBindingFrontend,
    ViewBindingOntology,
    ViewSpec,
)
from repo_ontology.translate import match_views, normalize_text
from repo_ontology.intake import RequirementItem, analyze_requirements, generate_markdown_report


def test_normalize_text():
    assert normalize_text("관리자/강사 > 데이터관리 > 출석체크") == "관리자 강사 데이터관리 출석체크"
    assert normalize_text("  S-COM-001  ") == "s com 001"


def test_match_views_by_page_code_and_menu():
    registry = OntologyRegistry(root_path=Path("/fake"), ontology_dir=Path("/fake/.ontology"))
    v1 = ViewSpec(
        view="AttendanceCheckView",
        page_code="ATT-001",
        menu="관리자/강사 > 데이터관리 > 수업데이터관리 > 출석체크",
        binding=ViewBinding(
            frontend=ViewBindingFrontend(route="/admin/attendance", slice="features/attendance"),
            backend=ViewBindingBackend(router="app/api/attendance.py", endpoints=["POST /attendance"]),
            ontology=ViewBindingOntology(objects=["Attendance"], actions=["RecordAttendance"]),
        )
    )
    v2 = ViewSpec(
        view="NoticeWriteView",
        page_code="P-TOOL-001",
        menu="관리자/강사 > 앱 관리(신규) > 공지 관리 > 공지 작성",
    )
    registry.views = {"AttendanceCheckView": v1, "NoticeWriteView": v2}

    # 1. Exact page_code match
    res_code = match_views(registry, "ATT-001")
    assert len(res_code) >= 1
    assert res_code[0][0].view == "AttendanceCheckView"
    assert res_code[0][1] == 100.0

    # 2. Substring in menu match
    res_menu = match_views(registry, "출석체크")
    assert len(res_menu) >= 1
    assert res_menu[0][0].view == "AttendanceCheckView"
    assert res_menu[0][1] >= 70.0

    # 3. Mobile page code
    res_mob = match_views(registry, "P-TOOL-001")
    assert len(res_mob) >= 1
    assert res_mob[0][0].view == "NoticeWriteView"


def test_analyze_requirements_and_report():
    registry = OntologyRegistry(root_path=Path("/fake"), ontology_dir=Path("/fake/.ontology"))
    v1 = ViewSpec(
        view="AttendanceCheckView",
        page_code="ATT-001",
        menu="관리자/강사 > 데이터관리 > 수업데이터관리 > 출석체크",
        binding=ViewBinding(
            frontend=ViewBindingFrontend(route="/admin/attendance", slice="features/attendance"),
            backend=ViewBindingBackend(router="app/api/attendance.py", endpoints=["POST /attendance"]),
            ontology=ViewBindingOntology(objects=["Attendance"], actions=["RecordAttendance"]),
        )
    )
    registry.views = {"AttendanceCheckView": v1}

    items = [
        RequirementItem(
            source_sheet="기타 웹 개선 사항",
            row_num=3,
            menu_path="데이터관리 > 수업데이터관리 > 출석체크",
            title="출석체크",
            description="조퇴/제외 추가",
        ),
        RequirementItem(
            source_sheet="기타 웹 개선 사항",
            row_num=10,
            menu_path="데이터관리 > 상담 기록 관리(신규) > 상담 기록 관리(신규)",
            title="상담 기록 관리(신규)",
            description="상담 기록 관리 탭 신설",
        ),
    ]

    matched, unmatched = analyze_requirements(registry, items)
    assert len(matched) == 1
    assert matched[0].matched_view.view == "AttendanceCheckView"
    assert len(unmatched) == 1
    assert "상담 기록 관리" in unmatched[0].title

    report = generate_markdown_report(registry, matched, unmatched, "test_spec.xlsx")
    assert "AttendanceCheckView" in report
    assert "/admin/attendance" in report
    assert "상담 기록 관리(신규)" in report
