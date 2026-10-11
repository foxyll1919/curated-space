---
type: "query"
date: "2026-10-11T11:54:28.928143+00:00"
question: "Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["create_item()", "Item", "Image upload firewall", "Gemini screenshot extraction pipeline"]
---

# Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?

## Answer

Expanded from graph vocabulary: [create, item, upload, fastapi, database, image, pipeline]. The AST graph shows main.py contains create_item(), and create_item() uses Item (the latter edge is marked INFERRED). Its connection represents the upload endpoint creating/persisting an Item row. The README describes the intended Image upload firewall -> Gemini screenshot extraction pipeline -> validated persistence path, but the graph has no edge from create_item() to the firewall or Gemini service. This matches the documented implementation gap: the route is not yet wired to the AI stages.

## Outcome

- Signal: useful

## Source Nodes

- create_item()
- Item
- Image upload firewall
- Gemini screenshot extraction pipeline