import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="./qmcp",
        args=["--confighome", "NAS27B823"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Initialization successful!")
            
            # List tools
            tools = await session.list_tools()
            print("Tools available:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

asyncio.run(run())
