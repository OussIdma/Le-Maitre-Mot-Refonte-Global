"""Module de gestion du curriculum officiel."""

from .loader import (
    CurriculumChapter,
    CurriculumIndex,
    load_curriculum_6e,
    get_curriculum_index,
    get_chapter_by_official_code,
    get_chapters_by_backend_name
)

__all__ = [
    "CurriculumChapter",
    "CurriculumIndex",
    "load_curriculum_6e",
    "get_curriculum_index",
    "get_chapter_by_official_code",
    "get_chapters_by_backend_name"
]
