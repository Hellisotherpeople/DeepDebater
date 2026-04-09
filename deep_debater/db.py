"""Database operations for debate evidence."""

from __future__ import annotations

import random
from typing import Callable

import duckdb
from ducksearch import search


def get_document_by_id(db_path: str, doc_id: int) -> dict | None:
    """Query bm25_tables.documents for a document by id."""
    con = duckdb.connect(db_path)
    result = con.execute(
        "SELECT * FROM bm25_tables.documents WHERE id = ?", [doc_id]
    ).fetchone()
    if result is None:
        con.close()
        return None
    colnames = [desc[0] for desc in con.description]
    con.close()
    return dict(zip(colnames, result))


def search_debate_cards(
    db_path: str,
    query: str,
    top_k: int = 10,
    on_results: Callable | None = None,
) -> list[dict]:
    """Search the debate evidence database using BM25.

    Returns a list of dicts with keys: id, tag, fullcite, markup.
    """
    result = search.documents(
        database=db_path,
        queries=[query],
        top_k=top_k,
        order_by="score DESC",
    )
    return_list = [
        {
            "id": r.get("id"),
            "tag": r.get("tag"),
            "fullcite": r.get("fullcite"),
            "markup": r.get("markup"),
        }
        for r in result[0]
    ]
    random.shuffle(return_list)
    if on_results is not None:
        on_results(return_list)
    return return_list


def make_search_fn(db_path: str):
    """Create a search function bound to a specific database path.

    This returns a callable with the signature expected by autogen's
    ``register_function``.
    """

    def _search(query: str) -> list:
        return search_debate_cards(db_path, query)

    _search.__name__ = "search_debate_cards"
    _search.__doc__ = (
        "Search the debate evidence dataset using natural language queries. "
        "Return a list of debate cards."
    )
    return _search
