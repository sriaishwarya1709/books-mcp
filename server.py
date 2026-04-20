from typing import Any, Dict, List
import json
import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# ─── MCP server definition ────────────────────────────────────────────────────
mcp = FastMCP(
    name="sample-mcp-server",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
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


# ─── Web host (what ACA needs) ───────────────────────────────────────────────
# Use the MCP app as the root ASGI app so its lifespan (task group) is
# properly initialized. Add a health check via middleware for ACA probes.
# DNS rebinding protection is disabled in FastMCP settings above since
# the server runs behind ACA's ingress proxy with a public FQDN.

class _ACAPatchMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path") == "/":
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


app = _ACAPatchMiddleware(mcp.streamable_http_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)