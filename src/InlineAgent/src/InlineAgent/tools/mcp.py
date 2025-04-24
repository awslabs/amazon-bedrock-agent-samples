from abc import ABC, abstractmethod
from contextlib import AsyncExitStack

from termcolor import colored

from pydantic import validate_call
from mcp import ClientSession, ListToolsResult, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from typing import Any, Callable, Dict, List

from InlineAgent.types.action_group import FunctionDefination
from InlineAgent.constants import TraceColor


class MCPServer(ABC):

    @validate_call
    async def set_available_tools(self, tools_to_use: set) -> List[FunctionDefination]:
        """
        Retrieve a list of available tools from the MCP server.
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        tools: ListToolsResult = await self.session.list_tools()
        tools_list = tools.tools

        function = {}
        for tool in tools_list:
            if len(tools_to_use) != 0:
                if tool.name in tools_to_use:
                    function = {
                        "description": tool.description,
                        "name": tool.name,
                        "parameters": {},
                        "requireConfirmation": "DISABLED",
                    }
                    # Process input schema properties
                    if "properties" in tool.inputSchema:

                        for param_name, param_details in tool.inputSchema[
                            "properties"
                        ].items():
                            function["parameters"][param_name] = {
                                "description": param_details.get(
                                    "description", param_name
                                ),
                                "type": param_details.get("type", "string"),
                                "required": param_name
                                in tool.inputSchema.get("required", []),
                            }

                        if len(function["parameters"]) > 5:

                            raise ValueError(
                                f"Tool {tool.name} has more than 5 parameters. This is not supported by Bedrock Agents."
                            )

                    if "functions" not in self.function_schema:
                        self.function_schema["functions"] = list()

                    self.function_schema["functions"].append(function)
            else:
                function = {
                    "description": tool.description,
                    "name": tool.name,
                    "parameters": {},
                    "requireConfirmation": "DISABLED",
                }
                # Process input schema properties
                if "properties" in tool.inputSchema:

                    for param_name, param_details in tool.inputSchema[
                        "properties"
                    ].items():
                        function["parameters"][param_name] = {
                            "description": param_details.get("description", param_name),
                            "type": param_details.get("type", "string"),
                            "required": param_name
                            in tool.inputSchema.get("required", []),
                        }

                    if len(function["parameters"]) > 5:

                        raise ValueError(
                            f"Tool {tool.name} has more than 5 parameters. This is not supported by Bedrock Agents."
                        )

                if "functions" not in self.function_schema:
                    self.function_schema["functions"] = list()

                self.function_schema["functions"].append(function)

    @validate_call
    async def set_callable_tool(self, tools_to_use: set) -> Dict[str, Callable]:
        """
        Get callable function
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        tools = await self.session.list_tools()
        tools_list = tools.tools

        # Helper factory function to create a callable with the correct tool name
        def create_callable(tool_name):
            async def callable(*args, **kwargs):
                response = await self.session.call_tool(
                    tool_name, arguments=kwargs
                )
                return response.content[0].text
            return callable

        for tool in tools_list:
            if len(tools_to_use) != 0:
                if tool.name in tools_to_use:
                    self.callable_tools[tool.name] = create_callable(tool.name)
            else:
                self.callable_tools[tool.name] = create_callable(tool.name)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


class MCPStdio(MCPServer):
    """
    A client class for interacting with the MCP (Model Control Protocol) server.
    """

    @classmethod
    @validate_call
    async def create(
        cls, server_params: StdioServerParameters, tools_to_use: set = set()
    ):
        # Initialize session and client objects
        self = cls()
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.function_schema = dict()
        self.callable_tools = dict()

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(
            colored(
                f"\nConnected to server with tools:{[tool.name for tool in tools]}",
                TraceColor.invocation_output,
            )
        )

        await self.set_available_tools(tools_to_use=tools_to_use)
        await self.set_callable_tool(tools_to_use=tools_to_use)

        return self


class MCPHttp(MCPServer):
    @classmethod
    @validate_call
    async def create(
        cls,
        url: str,
        headers: Dict[str, Any] = None,
        timeout: float = 5,
        sse_read_timeout: float = 60 * 5,
        tools_to_use: set = set(),
    ):

        # Initialize session and client objects
        self = cls()
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.function_schema = dict()
        self.callable_tools = dict()

        stdio_transport = await self.exit_stack.enter_async_context(
            sse_client(
                url=url,
                headers=headers,
                timeout=timeout,
                sse_read_timeout=sse_read_timeout,
            )
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(
            colored(
                f"\nConnected to server with tools:{[tool.name for tool in tools]}",
                TraceColor.invocation_output,
            )
        )

        await self.set_available_tools(tools_to_use=tools_to_use)
        await self.set_callable_tool(tools_to_use=tools_to_use)

        return self
