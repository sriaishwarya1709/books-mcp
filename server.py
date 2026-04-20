from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
import json
import os

# Initialize FastMCP server
mcp = FastMCP(
    name="sample-mcp-server",
    host="0.0.0.0",
    port=8000,
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "books.json")


def _load_books() -> List[Dict[str, Any]]:
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# ─── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool(
    name="get_book_by_title",
    description="Get a book by its exact title (case-insensitive).",
    structured_output=True,
)
def get_book_by_title(title: str) -> Dict[str, Any]:
    books = _load_books()
    for book in books:
        if book["title"].lower() == title.lower():
            return book
    return {"error": f"No book found with title '{title}'"}


@mcp.tool(
    name="get_book_by_id",
    description="Get a book by its numeric ID.",
    structured_output=True,
)
def get_book_by_id(id: int) -> Dict[str, Any]:
    books = _load_books()
    for book in books:
        if book["id"] == id:
            return book
    return {"error": f"No book found with id {id}"}


@mcp.tool(
    name="get_books_by_author",
    description="Get all books written by a given author (case-insensitive partial match).",
    structured_output=True,
)
def get_books_by_author(author: str) -> Dict[str, Any]:
    books = _load_books()
    matched = [b for b in books if author.lower() in b["author"].lower()]
    if not matched:
        return {"error": f"No books found for author '{author}'"}
    return {"books": matched}


@mcp.tool(
    name="get_books_by_genre",
    description="Get all books that belong to a specific genre (case-insensitive).",
    structured_output=True,
)
def get_books_by_genre(genre: str) -> Dict[str, Any]:
    books = _load_books()
    matched = [b for b in books if b.get("genre", "").lower() == genre.lower()]
    if not matched:
        return {"error": f"No books found in genre '{genre}'"}
    return {"books": matched}


@mcp.tool(
    name="get_books_by_min_rating",
    description="Get all books whose rating is greater than or equal to the provided minimum rating (0–5 scale).",
    structured_output=True,
)
def get_books_by_min_rating(min_rating: float) -> Dict[str, Any]:
    books = _load_books()
    matched = [b for b in books if b.get("rating", 0) >= min_rating]
    if not matched:
        return {"error": f"No books found with rating >= {min_rating}"}
    return {"books": matched}


@mcp.tool(
    name="get_all_books",
    description="Return the complete list of books in the catalog.",
    structured_output=True,
)
def get_all_books() -> Dict[str, Any]:
    return {"books": _load_books()}


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")
