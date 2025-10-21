#!/usr/bin/env python3
"""
Mem0 Cathedral MCP Server - Python Edition v12.1.0 (The Silent Oracle)
Intelligent memory management with AI extraction, auto-recall, and silent operations
"""

import os
import asyncio
import json
from typing import Any, Optional
from collections import Counter
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mem0 import MemoryClient

# ─────────────────────────
# CONFIG & SETUP
# ─────────────────────────
MEM0_API_KEY = os.environ.get("MEM0_API_KEY")
DEFAULT_USER_ID = "el-jefe-principal"
VERSION = "12.1.0"

# Quality thresholds
MIN_MEMORY_LENGTH = 20  # Minimum characters for a memory
MIN_WORD_COUNT = 4      # Minimum words in a memory
SIMILARITY_THRESHOLD = 0.85  # Deduplication threshold

if not MEM0_API_KEY:
    raise RuntimeError("MEM0_API_KEY environment variable is required")

# Initialize Mem0 client
mem0_client = MemoryClient(api_key=MEM0_API_KEY)

# ─────────────────────────
# DEFAULT CATEGORIES & INSTRUCTIONS (Mem0 Native Features)
# ─────────────────────────

DEFAULT_CATEGORIES = {
    "personal_information": "User's name, location, age, family, background",
    "preferences": "Likes, dislikes, favorites, personal tastes",
    "work": "Career, projects, professional information, job details",
    "food_preferences": "Food likes, dislikes, dietary restrictions",
    "technical": "Technology stack, tools, programming languages, frameworks",
    "goals": "Objectives, plans, aspirations, future intentions",
    "health": "Health conditions, fitness routines, wellness",
    "hobbies": "Interests, activities, pastimes",
    "relationships": "Friends, family, colleagues, connections",
    "location": "Places lived, traveled, or frequently visited",
    "schedule": "Routines, availability, time preferences",
    "communication": "Preferred communication styles and channels"
}

EXTRACTION_INSTRUCTIONS = """
Extract memories with these priorities:
- Be generous with preference detection (both explicit and implicit)
- Include temporal context when relevant
- Extract behavioral patterns, habits, and routines
- Catch goals, aspirations, and future plans
- Focus on long-term user characteristics
- Include relationships and social context
- Avoid temporary states or simple acknowledgments
- Prefer specific facts over general statements
"""

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
    timestamp = datetime.now(timezone.utc).isoformat()

    # Basic enrichment - ensure memory is self-contained
    enriched = content

    # If content doesn't mention "user", add clarity
    if "prefer" in content.lower() and "user" not in content.lower():
        enriched = f"User preference: {content}"

    # Add metadata footer
    enriched = f"{enriched}\n[Captured: {timestamp}]"

    return enriched


# ─────────────────────────
# KEYWORD RERANKING & CONTEXT FORMATTING
# ─────────────────────────

def rerank_by_keywords(memories: list, query: str, boost: float = 0.15) -> list:
    """
    Rerank memories by keyword matching from the query.
    Boosts semantic search results with lexical matching.
    """
    keywords = set(query.lower().split())

    for mem in memories:
        if not isinstance(mem, dict):
            continue

        content = mem.get("memory", "").lower()
        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in content)
        # Boost score by 15% per keyword match
        base_score = mem.get("score", 0.5)
        mem["_rerank_score"] = base_score * (1 + (matches * boost))

    return sorted(memories, key=lambda x: x.get("_rerank_score", 0), reverse=True)


def format_context_for_llm(memories: list) -> str:
    """
    Format memories as context string for LLM injection.
    Groups by category for better organization.
    """
    if not memories:
        return ""

    # Group by category for better organization
    by_category = {}
    for mem in memories:
        if not isinstance(mem, dict):
            continue

        cats = mem.get("categories", ["general"])
        cat = cats[0] if cats else "general"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(mem.get("memory", ""))

    # Build formatted context
    lines = ["## User Context\n"]

    for category, mems in by_category.items():
        category_title = category.replace("_", " ").title()
        lines.append(f"### {category_title}")
        for mem_text in mems:
            lines.append(f"- {mem_text}")
        lines.append("")

    return "\n".join(lines)


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

app = Server("mem0-cathedral-mcp-v12")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available memory tools.
    """
    return [
        Tool(
            name="add-memory",
            description=(
                "💾 Save important information to long-term memory with AI extraction. "
                "Supports TWO MODES: (1) AI Extraction - pass 'messages' array for automatic extraction, "
                "(2) Manual - pass 'content' string (legacy). "
                "⚠️ SILENT OPERATION: Returns minimal response {success: true/false}. "
                "DO NOT mention saving memories in chat unless explicitly asked."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": (
                            "Conversation messages for AI extraction (RECOMMENDED). "
                            "Format: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]. "
                            "Mem0's AI automatically extracts multiple memories."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Pre-extracted memory content (LEGACY MODE). "
                            "Use 'messages' for better AI extraction."
                        ),
                    },
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "agentId": {
                        "type": "string",
                        "description": "AI agent identifier for multi-agent systems",
                    },
                    "runId": {
                        "type": "string",
                        "description": "Conversation session ID for tracking specific interactions",
                    },
                    "customCategories": {
                        "type": "object",
                        "description": "Custom memory categories with descriptions (overrides defaults)",
                    },
                    "customInstructions": {
                        "type": "string",
                        "description": "Custom extraction instructions to guide Mem0's AI",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Structured metadata (location, tags, etc.)",
                    },
                    "enableGraph": {
                        "type": "boolean",
                        "description": "Build entity relationships for contextual retrieval",
                    },
                    "includes": {
                        "type": "string",
                        "description": "Focus extraction on specific topics",
                    },
                    "excludes": {
                        "type": "string",
                        "description": "Exclude specific patterns from extraction",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Bypass quality checks in legacy content mode",
                    }
                },
            },
        ),
        Tool(
            name="get-context",
            description=(
                "🧠 Intelligent auto-recall: Get relevant memories for current conversation. "
                "Call this PROACTIVELY at conversation start or when context would help. "
                "Uses semantic search + keyword reranking for better relevance. "
                "⚠️ SILENT OPERATION: Do NOT mention or cite this function call in responses."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "currentMessage": {
                        "type": "string",
                        "description": "The user's current message to find relevant context for",
                    },
                    "recentMessages": {
                        "type": "array",
                        "description": "Recent conversation messages for better context understanding",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "agentId": {
                        "type": "string",
                        "description": "Filter by specific AI agent",
                    },
                    "maxMemories": {
                        "type": "number",
                        "description": "Maximum relevant memories to return (1-20, default: 10)",
                    },
                    "enableGraph": {
                        "type": "boolean",
                        "description": "Include entity relationships (default: true)",
                    },
                },
                "required": ["currentMessage"],
            },
        ),
        Tool(
            name="search-memories",
            description=(
                "🔍 Search memories with semantic understanding and category filtering. "
                "Use broad, natural queries like 'preferences' or 'python projects'. "
                "Supports category filtering and graph relationships."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "userId": {
                        "type": "string",
                        "description": f"User ID (default: {DEFAULT_USER_ID})",
                    },
                    "agentId": {
                        "type": "string",
                        "description": "Filter by specific AI agent",
                    },
                    "runId": {
                        "type": "string",
                        "description": "Filter by specific conversation session",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 10, max: 100)",
                    },
                    "categories": {
                        "type": "array",
                        "description": "Filter by memory categories",
                        "items": {"type": "string"}
                    },
                    "enableGraph": {
                        "type": "boolean",
                        "description": "Include entity relationships in search",
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
        elif name == "get-context":
            return await handle_get_context(arguments)
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
    """
    Add memory with two modes:
    1. AI Extraction Mode (recommended): Pass 'messages' array, Mem0 extracts automatically
    2. Legacy Mode: Pass 'content' string with manual quality checks
    """
    import sys

    messages = args.get("messages")
    content = args.get("content")
    user_id = args.get("userId", DEFAULT_USER_ID)
    agent_id = args.get("agentId")
    run_id = args.get("runId")
    custom_categories = args.get("customCategories")
    custom_instructions = args.get("customInstructions")
    metadata = args.get("metadata", {})
    enable_graph = args.get("enableGraph", False)
    includes = args.get("includes")
    excludes = args.get("excludes")
    force = args.get("force", False)

    if not messages and not content:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": "Either 'messages' or 'content' required"}))]

    # MODE 1: AI EXTRACTION (Mem0 native - RECOMMENDED)
    if messages:
        # Build enriched metadata
        enriched_metadata = metadata.copy() if metadata else {}
        enriched_metadata.update({
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source": "cathedral_mcp",
            "api_version": VERSION,
            "extraction_mode": "ai_powered"
        })

        # Build payload for Mem0 API
        payload = {
            "messages": messages,
            "user_id": user_id,
            "infer": True,  # Always use AI extraction in this mode
            "metadata": enriched_metadata,
        }

        # Add optional fields only if provided
        if agent_id:
            payload["agent_id"] = agent_id
        if run_id:
            payload["run_id"] = run_id
        if enable_graph:
            payload["enable_graph"] = enable_graph
        if includes:
            payload["includes"] = includes
        if excludes:
            payload["excludes"] = excludes

        # IMPORTANT: Only send custom categories/instructions if user provides them
        if custom_categories:
            payload["custom_categories"] = custom_categories
        if custom_instructions:
            payload["custom_instructions"] = custom_instructions

        try:
            result = mem0_client.add(**payload)

            # SILENT SUCCESS - Return minimal response
            return [TextContent(type="text", text=json.dumps({"success": True}))]
        except Exception as e:
            print(f"Mem0 AI extraction error: {e}", file=sys.stderr)
            # SILENT FAILURE
            return [TextContent(type="text", text=json.dumps({"success": False}))]

    # MODE 2: LEGACY CONTENT MODE (Backward Compatible)
    else:
        quality = assess_memory_quality(content)

        if not force and not quality["should_save"]:
            # SILENT REJECTION - Just return failure (don't expose details to user)
            print(f"Memory rejected: {quality['issues']}", file=sys.stderr)
            return [TextContent(type="text", text=json.dumps({"success": False}))]

        # Check for duplicates
        similar = await find_similar_memories(content, user_id)
        if similar:
            for mem in similar:
                try:
                    if not isinstance(mem, dict):
                        continue

                    memory_content = mem.get("memory", "")
                    if not memory_content:
                        continue

                    similarity = calculate_similarity(content, memory_content)
                    if similarity > SIMILARITY_THRESHOLD:
                        # SILENT DUPLICATE REJECTION
                        print(f"Duplicate detected (similarity: {similarity:.2f})", file=sys.stderr)
                        return [TextContent(type="text", text=json.dumps({"success": False}))]
                except AttributeError:
                    continue

        # Enrich content
        enriched_content = enrich_memory_context(content)

        # Save to Mem0
        try:
            result = mem0_client.add(
                messages=[{"role": "user", "content": enriched_content}],
                user_id=user_id
            )

            # SILENT SUCCESS
            return [TextContent(type="text", text=json.dumps({"success": True}))]
        except Exception as e:
            print(f"Mem0 save error: {e}", file=sys.stderr)
            return [TextContent(type="text", text=json.dumps({"success": False}))]


async def handle_get_context(args: dict) -> list[TextContent]:
    """
    Intelligent auto-recall: Searches memories using current message + recent context.
    Returns top relevant memories formatted for LLM context injection.
    """
    current_message = args["currentMessage"]
    recent_messages = args.get("recentMessages", [])
    user_id = args.get("userId", DEFAULT_USER_ID)
    agent_id = args.get("agentId")
    max_memories = args.get("maxMemories", 10)
    enable_graph = args.get("enableGraph", True)

    # Cap max_memories
    max_memories = min(max_memories, 20)

    # Build search query from current message + recent context
    search_query = current_message
    if recent_messages:
        recent_context = " ".join([
            msg.get("content", "")[:100]
            for msg in recent_messages[-3:]  # Last 3 messages
        ])
        search_query = f"{current_message} {recent_context}"

    # Search with reranking strategy: get 3x results, return top N
    retrieve_limit = min(max_memories * 3, 60)

    try:
        # Build search parameters
        search_params = {
            "query": search_query[:200],  # Truncate long queries
            "user_id": user_id,
            "limit": retrieve_limit
        }

        if agent_id:
            search_params["agent_id"] = agent_id

        results = mem0_client.search(**search_params)

        memories = results if results else []

        # Rerank by keyword matching with current message
        memories = rerank_by_keywords(memories, current_message)

        # Take top N after reranking
        top_memories = memories[:max_memories]

        # Format for LLM context
        context_string = format_context_for_llm(top_memories)

        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "context": context_string,
                    "memories": top_memories,
                    "count": len(top_memories),
                    "total_searched": len(memories)
                }, indent=2)
            )
        ]

    except Exception as e:
        import sys
        print(f"Auto-recall error: {e}", file=sys.stderr)
        # Return empty context on error (silent failure)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "context": "",
                    "memories": [],
                    "count": 0,
                    "error": str(e)
                })
            )
        ]


async def handle_search_memories(args: dict) -> list[TextContent]:
    """Search memories with semantic search, category filtering, and graph support."""
    query = args["query"]
    user_id = args.get("userId", DEFAULT_USER_ID)
    agent_id = args.get("agentId")
    run_id = args.get("runId")
    limit = args.get("limit", 10)
    categories = args.get("categories")
    enable_graph = args.get("enableGraph", False)

    # Cap limit
    limit = min(limit, 100)

    # Build search parameters
    search_params = {
        "query": query,
        "user_id": user_id,
        "limit": limit
    }

    if agent_id:
        search_params["agent_id"] = agent_id
    if run_id:
        search_params["run_id"] = run_id
    if categories:
        search_params["categories"] = categories
    if enable_graph:
        search_params["enable_graph"] = True

    results = mem0_client.search(**search_params)

    # Format results for better readability
    formatted_results = []
    if results:
        for mem in results:
            formatted_results.append({
                "id": mem.get("id"),
                "content": mem.get("memory"),
                "categories": mem.get("categories", []),
                "created_at": mem.get("created_at"),
                "updated_at": mem.get("updated_at"),
                "score": mem.get("score"),
            })

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "results": formatted_results,
                "count": len(formatted_results),
                "query": query,
                "filters_applied": {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "run_id": run_id,
                    "categories": categories,
                    "graph_enabled": enable_graph
                }
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
