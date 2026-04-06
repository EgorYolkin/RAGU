from src.retrieve.lexical import build_match_query, build_title_match_query


def test_build_match_query_filters_stop_words_and_short_tokens() -> None:
    result = build_match_query("что я писал про obsidian graph?")
    # "что", "я", "про" are stop words or <3 chars — filtered out
    assert result == '"писал" OR "про" OR "obsidian" OR "graph"'


def test_build_match_query_deduplicates_tokens() -> None:
    assert build_match_query("rag rag graph") == '"rag" OR "graph"'


def test_build_match_query_empty_when_all_stop_words() -> None:
    assert build_match_query("а и в на из") == ""


def test_build_title_match_query_wraps_in_title_scope() -> None:
    result = build_title_match_query("golang программирование")
    assert result == 'title:("golang" OR "программирование")'


def test_build_title_match_query_empty_on_stop_words_only() -> None:
    assert build_title_match_query("на из в") == ""
