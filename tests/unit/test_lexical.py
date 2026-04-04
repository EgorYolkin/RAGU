from src.retrieve.lexical import build_match_query


def test_build_match_query_strips_punctuation_and_quotes_tokens() -> None:
    assert (
        build_match_query("что я писал про obsidian graph?")
        == '"что" OR "я" OR "писал" OR "про" OR "obsidian" OR "graph"'
    )


def test_build_match_query_deduplicates_tokens() -> None:
    assert build_match_query("rag rag graph") == '"rag" OR "graph"'
