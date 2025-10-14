#!/usr/bin/env python3
"""
Mem0 Cathedral MCP Server - Python Edition
Intelligent memory management with quality filtering and smart search
"""

import os
import asyncio
import json
from typing import Any, Optional
from collections import Counter
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mem0 import MemoryClient

# ─────────────────────────
# CONFIG & SETUP
# ─────────────────────────
MEM0_API_KEY = os.environ.get("MEM0_API_KEY")
DEFAULT_USER_ID = "el-jefe-principal"

# Quality thresholds
MIN_MEMORY_LENGTH = 20  # Minimum characters for a memory
MIN_WORD_COUNT = 4      # Minimum words in a memory
SIMILARITY_THRESHOLD = 0.85  # Deduplication threshold

if not MEM0_API_KEY:
    raise RuntimeError("MEM0_API_KEY environment variable is required")

# Initialize Mem0 client
mem0_client = MemoryClient(api_key=MEM0_API_KEY)

# ─────────────────────────
# QUALITY FILTERING
# ─────────────────────────

def assess_memory_quality(content: str) -> dict[str, Any]:
    """
    Assess the quality of memory content before saving.
    Returns a dict with quality metrics and whether to save.
    """
    quality = {
        "should_save": True,
        "issues": [],
        "score": 100
    }

    # Check length
    if len(content) < MIN_MEMORY_LENGTH:
        quality["should_save"] = False
        quality["issues"].append(f"Too short (min {MIN_MEMORY_LENGTH} chars)")
        quality["score"] -= 50

    # Check word count
    word_count = len(content.split())
    if word_count < MIN_WORD_COUNT:
        quality["should_save"] = False
        quality["issues"].append(f"Too few words (min {MIN_WORD_COUNT} words)")
        quality["score"] -= 30

    # Check for low-value patterns
    low_value_patterns = [
        "ok", "okay", "got it", "understood", "sure", "thanks", "thank you",
        "yes", "no", "maybe", "i see", "alright", "cool", "nice"
    ]

    content_lower = content.lower().strip()
    if content_lower in low_value_patterns:
        quality["should_save"] = False
        quality["issues"].append("Low-value acknowledgment")
        quality["score"] -= 40

    # Check for contextual information (good indicators)
    good_indicators = [
        "prefer", "like", "love", "hate", "dislike", "always", "never",
        "project", "work", "use", "technology", "tool", "language",
        "name is", "location", "timezone", "schedule", "routine",
        "goal", "objective", "plan", "want to", "need to"
    ]

    has_context = any(indicator in content_lower for indicator in good_indicators)
    if has_context:
        quality["score"] += 20

    # Penalize very long content (likely not a clean memory)
    if len(content) > 500:
        quality["score"] -= 10
        quality["issues"].append("Very long (may need summarization)")

    return quality


def enrich_memory_context(content: str, conversation_context: Optional[str] = None) -> str:
    """
    Enrich memory with additional context to make it more useful.
    """
    # Add timestamp context
    timestamp = datetime.utcnow().isoformat()

    # Basic enrichment - ensure memory is self-contained
    enriched = content

    # If content doesn't mention "user", add clarity
    if "prefer" in content.lower() and "user" not in content.lower():
        enriched = f"User preference: {content}"

    # Add metadata footer
    enriched = f"{enriched}\n[Captured: {timestamp}]"

    return enriched


# ─────────────────────────
# DEDUPLICATION
# ─────────────────────────

async def find_similar_memories(content: str, user_id: str, limit: int = 5) -> list[dict]:
    """
    Search for similar memories to avoid duplicates.
    Uses Mem0's semantic search.
    """
    try:
        # Extract key terms for search
        words = content.lower().split()
        # Remove common words
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        key_terms = [w for w in words if w not in stopwords]

        if not key_terms:
            return []

        # Search using a subset of key terms
        search_query = " ".join(key_terms[:5])

        results = mem0_client.search(
            query=search_query,
            user_id=user_id,
            limit=limit
        )

        return results if results else []
    except Exception as e:
        print(f"Error searching for similar memories: {e}", file=__import__('sys').stderr)
        return []


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple word-based similarity between two texts.
    Returns a score between 0 and 1.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0


# ─────────────────────────
# MCP SERVER
# ─────────────────────────

app = Server("mem0-cathedral-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available memory tools.
    """
    return [
        Tool(
            name="add-memory",
            description=(
                "Save important, contextualized information to long-term memory. "
                "Only call this for HIGH-VALUE information: user preferences, project details, "
                "technical decisions, personal facts, goals, or workflow patterns. "
                "DO NOT save: greetings, acknowledgments, casual chat, or repetitive info. "
                "Quality over quantity - each memory should be self-contained and useful."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": (
                            "Self-contained memory with full context. "
                            "GOOD: 'User prefers Python over JavaScript for backend services due to better ML library support.' "
                            "BAD: 'likes python' or 'ok got it'"
                        ),
                    },
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Bypass quality checks (use sparingly)",
                    }
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="search-memories",
            description=(
                "Search memories with semantic understanding. Call this EARLY in conversations "
                "when the user: mentions past discussions, asks questions you might have context for, "
                "discusses topics they've mentioned before, or requests recommendations. "
                "Use broad, natural queries like 'preferences' or 'python projects' rather than exact matches."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Examples: 'coding preferences', 'work projects', 'tools user dislikes'",
                    },
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 10, max: 50)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get-all-memories",
            description=(
                "Retrieve ALL memories for a user. Use this at conversation start to load context, "
                "or when user asks 'what do you know about me?' or 'show me everything you remember'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                },
            },
        ),
        Tool(
            name="update-memory",
            description="Update an existing memory when information changes or needs correction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memoryId": {
                        "type": "string",
                        "description": "ID of memory to update",
                    },
                    "content": {
                        "type": "string",
                        "description": "New memory content",
                    },
                },
                "required": ["memoryId", "content"],
            },
        ),
        Tool(
            name="delete-memory",
            description="Permanently delete a specific memory. Use when user explicitly asks to forget something.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memoryId": {
                        "type": "string",
                        "description": "ID of memory to delete",
                    },
                },
                "required": ["memoryId"],
            },
        ),
        Tool(
            name="consolidate-memories",
            description=(
                "Merge similar or redundant memories to improve quality. "
                "Use when you notice duplicate information or want to clean up memory storage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "dryRun": {
                        "type": "boolean",
                        "description": "Preview consolidation without making changes",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls.
    """
    try:
        if name == "add-memory":
            return await handle_add_memory(arguments)
        elif name == "search-memories":
            return await handle_search_memories(arguments)
        elif name == "get-all-memories":
            return await handle_get_all_memories(arguments)
        elif name == "update-memory":
            return await handle_update_memory(arguments)
        elif name == "delete-memory":
            return await handle_delete_memory(arguments)
        elif name == "consolidate-memories":
            return await handle_consolidate_memories(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "tool": name
                }, indent=2)
            )
        ]


async def handle_add_memory(args: dict) -> list[TextContent]:
    """Add a new memory with quality filtering."""
    content = args["content"]
    user_id = args.get("userId", DEFAULT_USER_ID)
    force = args.get("force", False)

    # Assess quality
    quality = assess_memory_quality(content)

    if not force and not quality["should_save"]:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "ok": False,
                    "rejected": True,
                    "reason": "Quality threshold not met",
                    "issues": quality["issues"],
                    "suggestion": "Provide more context or use 'force: true' to override",
                }, indent=2)
            )
        ]

    # Check for duplicates
    similar = await find_similar_memories(content, user_id)
    if similar:
        for mem in similar:
            # Handle case where mem might not be a dict
            try:
                if not isinstance(mem, dict):
                    print(f"WARNING: Unexpected memory format: {type(mem)}", file=__import__('sys').stderr)
                    continue

                memory_content = mem.get("memory", "")
                if not memory_content:
                    continue

                similarity = calculate_similarity(content, memory_content)
                if similarity > SIMILARITY_THRESHOLD:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "ok": False,
                                "duplicate": True,
                                "existing_memory_id": mem.get("id"),
                                "existing_content": memory_content,
                                "similarity": round(similarity, 2),
                                "suggestion": "Use update-memory to modify existing memory instead",
                            }, indent=2)
                        )
                    ]
            except AttributeError as e:
                print(f"WARNING: Duplicate check failed: {e}", file=__import__('sys').stderr)
                continue

    # Enrich content
    enriched_content = enrich_memory_context(content)

    # Save to Mem0
    result = mem0_client.add(
        messages=[{"role": "user", "content": enriched_content}],
        user_id=user_id
    )

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "ok": True,
                "memory_id": result.get("id") if isinstance(result, dict) else result[0].get("id"),
                "quality_score": quality["score"],
                "message": "Memory saved successfully",
            }, indent=2)
        )
    ]


async def handle_search_memories(args: dict) -> list[TextContent]:
    """Search memories with semantic search."""
    query = args["query"]
    user_id = args.get("userId", DEFAULT_USER_ID)
    limit = args.get("limit", 10)

    # Cap limit
    limit = min(limit, 50)

    results = mem0_client.search(
        query=query,
        user_id=user_id,
        limit=limit
    )

    # Format results for better readability
    formatted_results = []
    if results:
        for mem in results:
            formatted_results.append({
                "id": mem.get("id"),
                "content": mem.get("memory"),
                "created_at": mem.get("created_at"),
                "updated_at": mem.get("updated_at"),
            })

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "results": formatted_results,
                "count": len(formatted_results),
                "query": query,
            }, indent=2)
        )
    ]


async def handle_get_all_memories(args: dict) -> list[TextContent]:
    """Get all memories for a user."""
    user_id = args.get("userId", DEFAULT_USER_ID)

    memories = mem0_client.get_all(user_id=user_id)

    # Format results
    formatted = []
    if memories:
        for mem in memories:
            formatted.append({
                "id": mem.get("id"),
                "content": mem.get("memory"),
                "created_at": mem.get("created_at"),
                "updated_at": mem.get("updated_at"),
            })

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "memories": formatted,
                "total": len(formatted),
            }, indent=2)
        )
    ]


async def handle_update_memory(args: dict) -> list[TextContent]:
    """Update an existing memory."""
    memory_id = args["memoryId"]
    content = args["content"]

    result = mem0_client.update(
        memory_id=memory_id,
        data=content
    )

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "ok": True,
                "memory_id": memory_id,
                "message": "Memory updated successfully",
            }, indent=2)
        )
    ]


async def handle_delete_memory(args: dict) -> list[TextContent]:
    """Delete a memory."""
    memory_id = args["memoryId"]

    mem0_client.delete(memory_id=memory_id)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "ok": True,
                "memory_id": memory_id,
                "message": "Memory deleted successfully",
            }, indent=2)
        )
    ]


async def handle_consolidate_memories(args: dict) -> list[TextContent]:
    """Find and merge similar memories."""
    user_id = args.get("userId", DEFAULT_USER_ID)
    dry_run = args.get("dryRun", True)

    # Get all memories
    all_memories = mem0_client.get_all(user_id=user_id)

    if not all_memories:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "ok": True,
                    "message": "No memories to consolidate",
                }, indent=2)
            )
        ]

    # Find similar pairs
    consolidation_candidates = []
    checked = set()

    for i, mem1 in enumerate(all_memories):
        for j, mem2 in enumerate(all_memories[i+1:], start=i+1):
            pair_key = f"{i}-{j}"
            if pair_key in checked:
                continue

            checked.add(pair_key)

            content1 = mem1.get("memory", "")
            content2 = mem2.get("memory", "")

            similarity = calculate_similarity(content1, content2)

            if similarity > 0.7:  # Lower threshold for consolidation
                consolidation_candidates.append({
                    "memory1_id": mem1.get("id"),
                    "memory1_content": content1,
                    "memory2_id": mem2.get("id"),
                    "memory2_content": content2,
                    "similarity": round(similarity, 2),
                })

    if not consolidation_candidates:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "ok": True,
                    "message": "No similar memories found to consolidate",
                    "total_memories": len(all_memories),
                }, indent=2)
            )
        ]

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "ok": True,
                "dry_run": dry_run,
                "candidates": consolidation_candidates,
                "count": len(consolidation_candidates),
                "message": "Review these candidates. Use update-memory and delete-memory to consolidate manually.",
            }, indent=2)
        )
    ]


# ─────────────────────────
# START SERVER
# ─────────────────────────

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
