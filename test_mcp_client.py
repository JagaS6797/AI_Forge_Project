import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "arxiv_mcp_server"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            print(f"Tools found: {tool_names}")
            
            if "search_papers" not in tool_names:
                print("Error: search_papers tool not found")
                return

            # Call search_papers
            result = await session.call_tool("search_papers", arguments={"query": "transformers", "max_results": 2})
            
            print(f"Result type: {type(result)}")
            print(f"Content type: {type(result.content)}")
            if result.content:
                print(f"First content item type: {type(result.content[0])}")
                # Print a bit of the text attribute if it exists
                text_preview = result.content[0].text[:200] if hasattr(result.content[0], 'text') else "No text attr"
                print(f"Content[0] text preview: {text_preview}")

if __name__ == "__main__":
    asyncio.run(main())
