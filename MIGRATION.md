# Migration Guide: Node.js → Python

Quick guide to switch from the v1.0 Node.js version to v2.0 Python version.

## Why Migrate?

The Python version solves the key issues:

1. **Fewer, better memories** - Quality filtering prevents spam
2. **No duplicates** - Automatic deduplication before save
3. **Search works better** - Clearer tool descriptions trigger more reliably
4. **Native SDK** - Uses official Mem0 Python SDK
5. **Memory consolidation** - New tool to clean up old junk

## Migration Steps

### 1. Install Python Dependencies

```bash
cd C:\mcptools\mem0-cathedral-mcp
pip install -r requirements.txt
```

Or with uv (faster):
```bash
uv pip install -r requirements.txt
```

### 2. Update Claude Desktop Config

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

**Before (Node.js):**
```json
{
  "mcpServers": {
    "mem0": {
      "command": "node",
      "args": ["C:\\mcptools\\mem0-cathedral-mcp\\index.js"],
      "env": {
        "MEM0_API_KEY": "your_key_here"
      }
    }
  }
}
```

**After (Python):**
```json
{
  "mcpServers": {
    "mem0": {
      "command": "python",
      "args": ["C:\\mcptools\\mem0-cathedral-mcp\\server.py"],
      "env": {
        "MEM0_API_KEY": "your_key_here"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop completely.

### 4. Test Basic Functionality

Try adding a memory:
```
User: Remember that I prefer Python over JavaScript
Claude: [Should call add-memory and succeed]
```

Try searching:
```
User: What languages do I prefer?
Claude: [Should call search-memories and find your preference]
```

### 5. Clean Up Old Memories (Optional)

If you have many low-quality memories from v1.0:

```
User: Run memory consolidation in dry-run mode
Claude: [Calls consolidate-memories with dryRun: true]
```

Review the candidates, then manually merge/delete as needed.

## Key Differences

### Tool Changes

| Tool | v1.0 (Node.js) | v2.0 (Python) | Notes |
|------|---------------|---------------|-------|
| add-memory | ✅ | ✅ | Now has quality filtering |
| search-memories | ✅ | ✅ | Better prompting |
| get-memory | ✅ | ❌ | Removed (rarely used) |
| get-all-memories | ❌ | ✅ | New! Better than get-memory |
| update-memory | ✅ | ✅ | Same |
| delete-memory | ✅ | ✅ | Same |
| get-memory-history | ✅ | ❌ | Removed (rarely used) |
| consolidate-memories | ❌ | ✅ | New! Finds duplicates |

### Behavior Changes

**Add Memory:**
- **v1.0**: Saved everything, even "ok" and "thanks"
- **v2.0**: Rejects low-quality content, checks for duplicates

**Search:**
- **v1.0**: Verbose description, rarely triggered
- **v2.0**: Concise description, triggers more reliably

## Rollback Plan

If you need to revert to Node.js:

1. Keep both `index.js` and `server.py` in the directory
2. Change config back to:
   ```json
   "command": "node",
   "args": ["C:\\mcptools\\mem0-cathedral-mcp\\index.js"]
   ```
3. Restart Claude Desktop

No data loss - same Mem0 API backend!

## Troubleshooting Migration

### "ModuleNotFoundError: No module named 'mcp'"

```bash
pip install mcp mem0ai
```

### "Python was not found"

Install Python 3.10+ from python.org or Microsoft Store.

### Server not responding

Check logs:
```
%APPDATA%\Claude\logs\mcp-server-mem0.log
```

### Too strict filtering

Edit `server.py` line 23-25 to lower thresholds:
```python
MIN_MEMORY_LENGTH = 10   # Was 20
MIN_WORD_COUNT = 2       # Was 4
```

## Questions?

Check the main [README.md](README.md) for full documentation.
