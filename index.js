#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

// ─────────────────────────
// CONFIG & SETUP
// ─────────────────────────
const MEM0_API_KEY = process.env.MEM0_API_KEY;
const MEM0_API_URL = 'https://api.mem0.ai/v1';
const MEM0_API_V2_URL = 'https://api.mem0.ai/v2';
const DEFAULT_USER_ID = 'el-jefe-principal';

if (!MEM0_API_KEY) {
  console.error('Error: MEM0_API_KEY environment variable is required');
  process.exit(1);
}

// ─────────────────────────
// HELPER FUNCTIONS
// ─────────────────────────
async function makeMem0Request(endpoint, method = 'GET', body = null) {
  const headers = {
    'Authorization': `Token ${MEM0_API_KEY}`,
    'Content-Type': 'application/json',
  };

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${MEM0_API_URL}${endpoint}`, options);

  if (response.status === 204) {
    return { status: 'success' };
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Mem0 API error (${response.status}): ${errorText}`);
  }

  return await response.json();
}

// ─────────────────────────
// MCP SERVER
// ─────────────────────────
const server = new Server(
  {
    name: 'mem0-cathedral-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// ─────────────────────────
// TOOL DEFINITIONS
// ─────────────────────────
const tools = [
  {
    name: 'add-memory',
    description: 'Add a new memory. Call this when the user shares information about themselves, their preferences, or anything relevant for future conversations. Also use when the user explicitly asks you to remember something.',
    inputSchema: {
      type: 'object',
      properties: {
        content: {
          type: 'string',
          description: 'The content to store in memory',
        },
        userId: {
          type: 'string',
          description: `User ID for memory storage. If not provided explicitly, use 'el-jefe-principal'`,
        },
      },
      required: ['content'],
    },
  },
  {
    name: 'search-memories',
    description: 'Search through stored memories. Call this ANYTIME the user asks a question that might be answered by their previous conversations or stored information.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: "The search query based on what the user is asking. Examples: 'What did I tell you about the weather last week?' or 'What did I tell you about my friend John?'",
        },
        userId: {
          type: 'string',
          description: `User ID for memory storage. If not provided explicitly, use 'el-jefe-principal'`,
        },
        limit: {
          type: 'number',
          description: 'Maximum number of memories to return (default: 100)',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'get-memory',
    description: 'Retrieve a specific memory by its ID. Use this when you have a memory ID and need to see its full details.',
    inputSchema: {
      type: 'object',
      properties: {
        memoryId: {
          type: 'string',
          description: 'The unique ID of the memory to retrieve',
        },
      },
      required: ['memoryId'],
    },
  },
  {
    name: 'update-memory',
    description: 'Update the content of an existing memory. Use this when the user wants to modify or correct something they previously told you.',
    inputSchema: {
      type: 'object',
      properties: {
        memoryId: {
          type: 'string',
          description: 'The unique ID of the memory to update',
        },
        text: {
          type: 'string',
          description: 'The new content for the memory',
        },
        userId: {
          type: 'string',
          description: `User ID for context. If not provided explicitly, use 'el-jefe-principal'`,
        },
      },
      required: ['memoryId', 'text'],
    },
  },
  {
    name: 'delete-memory',
    description: 'Permanently delete a memory. Use this when the user explicitly asks to forget or remove specific information.',
    inputSchema: {
      type: 'object',
      properties: {
        memoryId: {
          type: 'string',
          description: 'The unique ID of the memory to delete',
        },
      },
      required: ['memoryId'],
    },
  },
  {
    name: 'get-memory-history',
    description: 'View the modification history of a specific memory. Use this to see how a memory has changed over time.',
    inputSchema: {
      type: 'object',
      properties: {
        memoryId: {
          type: 'string',
          description: 'The unique ID of the memory to get history for',
        },
      },
      required: ['memoryId'],
    },
  },
];

// ─────────────────────────
// REQUEST HANDLERS
// ─────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'add-memory': {
        const userId = args.userId || DEFAULT_USER_ID;
        const payload = {
          messages: [{ role: 'user', content: args.content }],
          user_id: userId,
        };

        const result = await makeMem0Request('/memories/', 'POST', payload);

        if (result && result.length > 0) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  ok: true,
                  memory_id: result[0].id,
                  message: 'Memory added successfully',
                }, null, 2),
              },
            ],
          };
        } else {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  ok: false,
                  error: 'API returned an empty response, memory not created',
                }, null, 2),
              },
            ],
          };
        }
      }

      case 'search-memories': {
        const userId = args.userId || DEFAULT_USER_ID;
        const limit = args.limit || 100;

        // Use v2 API for search with top_k parameter to support higher limits
        const payload = {
          query: args.query,
          version: 'v2',
          filters: {
            user_id: userId,
          },
          top_k: limit,
        };

        const headers = {
          'Authorization': `Token ${MEM0_API_KEY}`,
          'Content-Type': 'application/json',
        };

        const response = await fetch(`${MEM0_API_V2_URL}/memories/search/`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Mem0 API error (${response.status}): ${errorText}`);
        }

        const result = await response.json();

        // v2 API returns {results: [...]} format
        let memories = [];
        if (result && result.results && Array.isArray(result.results)) {
          memories = result.results;
        } else if (Array.isArray(result)) {
          memories = result;
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                memories,
                count: memories.length,
              }, null, 2),
            },
          ],
        };
      }

      case 'get-memory': {
        const result = await makeMem0Request(`/memories/${args.memoryId}/`);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'update-memory': {
        const userId = args.userId || DEFAULT_USER_ID;
        const payload = {
          text: args.text,
          user_id: userId,
        };

        const result = await makeMem0Request(
          `/memories/${args.memoryId}/`,
          'PUT',
          payload
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                ok: true,
                message: 'Memory updated successfully',
                data: result,
              }, null, 2),
            },
          ],
        };
      }

      case 'delete-memory': {
        await makeMem0Request(`/memories/${args.memoryId}/`, 'DELETE');

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                status: 'success',
                message: `Memory ${args.memoryId} has been deleted`,
              }, null, 2),
            },
          ],
        };
      }

      case 'get-memory-history': {
        const result = await makeMem0Request(`/memories/${args.memoryId}/history/`);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            error: error.message,
            tool: name,
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// ─────────────────────────
// START SERVER
// ─────────────────────────
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Mem0 Cathedral MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
