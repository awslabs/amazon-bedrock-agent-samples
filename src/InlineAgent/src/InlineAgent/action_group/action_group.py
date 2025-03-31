import json
from functools import cached_property
import re
from typing import (
    Annotated,
    List,
    Dict,
    Any,
    Callable,
    Literal,
    Optional,
    Self,
    Tuple,
    Union,
)
from inspect import Parameter, signature
import boto3
from pydantic import BaseModel, computed_field, model_validator, validate_call, Field

from InlineAgent.tools import MCPServer
from InlineAgent.types import APISchema, Executor, FunctionDefination


class ActionGroup(BaseModel):
    name: str
    description: Optional[str] = None
    tools: List[Callable] = Field(default_factory=list)
    lambda_name: str = None
    function_schema: List[FunctionDefination] = Field(default_factory=list)
    api_schema: Optional[APISchema] = None
    mcp_clients: Optional[List[MCPServer]] = Field(default_factory=list)
    profile: str = "default"
    builtin_tools: Dict[
        Literal["parentActionGroupSignature", "parentActionGroupSignatureParams"],
        Union[str, Dict],
    ] = Field(default_factory=dict)
    argument_key: str = "Parameters:"
    return_key: str = "Returns:"
    test: bool = False

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"

    @computed_field
    @property
    def executor(self) -> Executor:
        if self.tools:
            return Executor.RETURN_CONTROL
        if self.lambda_name and (self.api_schema or self.function_schema):
            return Executor.LAMBDA

        if self.mcp_clients:
            return Executor.RETURN_CONTROL

        if self.builtin_tools:
            return Executor.INBUILT_TOOL

        return None

    @computed_field
    @cached_property
    def session(self) -> Union[boto3.Session, None]:
        """Lazy loading of AWS session"""
        if self.test:
            return None
        print(
            f"Using `{self.profile}` [profile](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html)."
        )
        return boto3.Session(profile_name=self.profile)

    @computed_field
    @cached_property
    def aws_credentials(self) -> tuple[str, str]:
        """Cached AWS credentials"""

        try:
            if self.test:
                return "Mock-Account", "Mock-Region"
            sts_client = self.session.client("sts")
            identity = sts_client.get_caller_identity()
            return identity["Account"], self.session.region_name
        except Exception as e:
            return "Mock-Account", "Mock-Region"

    @computed_field
    @property
    def lamnda_arn(self) -> str:
        account_id, region = self.aws_credentials
        return f"arn:aws:lambda:{region}:{account_id}:function:{self.lambda_name}"

    @model_validator(mode="after")
    def check_correct_action_defination(self) -> Self:
        if (
            not self.tools
            and not self.lambda_name
            and not self.function_schema
            and not self.api_schema
            and not self.mcp_clients
            and not self.builtin_tools
        ):
            raise ValueError(
                "Either tools or mcp_clients or lambda_name & (function_schema or api_schema) or builtin_tools must be present..."
            )
        if self.tools:
            if self.lambda_name:
                raise ValueError(
                    "lambda_name is not supported when tools is present..."
                )
            if self.function_schema:
                raise ValueError(
                    "function_schema is not supported when tools is present..."
                )
            if self.mcp_clients:
                raise ValueError(
                    "mcp_clients is not supported when tools is present..."
                )

            if self.builtin_tools:
                raise ValueError(
                    "builtin_tools is not supported when tools is present..."
                )

        if self.lambda_name:
            if self.tools:
                raise ValueError(
                    "tools is not supported when lambda_name is present..."
                )

            if not self.function_schema and not self.api_schema:
                raise ValueError(
                    "One of function_schema or api_schema is required when lambda_name is present..."
                )
            elif self.function_schema and self.api_schema:
                raise ValueError(
                    "Only one of function_schema or api_schema is allowed when lambda_name is present..."
                )

            if self.mcp_clients:
                raise ValueError(
                    "mcp_clients is not supported when lambda_name is present..."
                )

            if self.builtin_tools:
                raise ValueError(
                    "builtin_tools is not supported when lambda_name is present..."
                )

        if self.function_schema:
            if self.tools:
                raise ValueError(
                    "tools is not supported when function_schema is present..."
                )

            if not self.lambda_name:
                raise ValueError(
                    "lambda_name is required when function_schema is present..."
                )

            if self.api_schema:
                raise ValueError(
                    "api_schema is not supported when function_schema is present..."
                )

            if self.mcp_clients:
                raise ValueError(
                    "mcp_clients is not supported when function_schema is present..."
                )

            if self.builtin_tools:
                raise ValueError(
                    "builtin_tools is not supported when function_schema is present..."
                )

        if self.api_schema:
            if self.tools:
                raise ValueError(
                    "tools is not supported when function_schema is present..."
                )

            if not self.lambda_name:
                raise ValueError(
                    "lambda_name is required when function_schema is present..."
                )

            if self.function_schema:
                raise ValueError(
                    "function_schema is not supported when api_schema is present..."
                )

            if self.mcp_clients:
                raise ValueError(
                    "mcp_clients is not supported when function_schema is present..."
                )

            if self.builtin_tools:
                raise ValueError(
                    "builtin_tools is not supported when function_schema is present..."
                )

        if self.mcp_clients:
            if self.tools:
                raise ValueError(
                    "tools is not supported when mcp_clients is present..."
                )
            if self.function_schema:
                raise ValueError(
                    "function_schema is not supported when mcp_clients is present..."
                )
            if self.lambda_name:
                raise ValueError(
                    "lambda_name is not supported when mcp_clients is present..."
                )

            if self.builtin_tools:
                raise ValueError(
                    "builtin_tools is not supported when mcp_clients is present..."
                )

        if self.builtin_tools:
            if self.tools:
                raise ValueError(
                    "tools is not supported when builtin_tools is present..."
                )
            if self.function_schema:
                raise ValueError(
                    "function_schema is not supported when builtin_tools is present..."
                )
            if self.lambda_name:
                raise ValueError(
                    "lambda_name is not supported when builtin_tools is present..."
                )

            if self.mcp_clients:
                raise ValueError(
                    "mcp_clients is not supported when builtin_tools is present..."
                )
        return self


class ActionGroups(BaseModel):
    action_groups: List[ActionGroup]

    @computed_field
    @property
    def tool_map(self) -> Dict[str, Callable]:
        tool_map = dict()

        for action_group in self.action_groups:
            if action_group.executor == Executor.RETURN_CONTROL:

                if action_group.tools:
                    for tool in action_group.tools:
                        tool_map[tool.__name__] = tool

                if action_group.mcp_clients:

                    for current_client in action_group.mcp_clients:
                        tool_map.update(current_client.callable_tools)

        return tool_map

    @computed_field
    @property
    def actionGroups(self) -> List:
        actionGroups = list()

        for action_group in self.action_groups:
            actionGroup = dict()
            actionGroup["actionGroupName"] = action_group.name
            if action_group.description:
                actionGroup["description"] = action_group.description

            if action_group.executor == Executor.RETURN_CONTROL:
                actionGroup["actionGroupExecutor"] = {
                    "customControl": action_group.executor.value
                }

                if action_group.mcp_clients:
                    function_schema = {"functions": list()}
                    for current_client in action_group.mcp_clients:
                        function_schema["functions"].extend(
                            current_client.function_schema["functions"]
                        )

                    actionGroup["functionSchema"] = function_schema
                else:
                    actionGroup["functionSchema"] = {
                        "functions": [
                            ActionGroupBuilder.create_function_schema(
                                func=func,
                                argument_key=action_group.argument_key,
                                return_key=action_group.return_key,
                            )
                            for func in action_group.tools
                        ],
                    }
            elif action_group.executor == Executor.LAMBDA:
                actionGroup["actionGroupExecutor"] = {"lambda": action_group.lamnda_arn}

                if action_group.function_schema:
                    actionGroup["functionSchema"] = {
                        "functions": [
                            function_schema.model_dump()
                            for function_schema in action_group.function_schema
                        ],
                    }
                elif action_group.api_schema:
                    actionGroup["apiSchema"] = {
                        "payload": action_group.api_schema.payload,
                        "s3": {
                            "s3BucketName": action_group.api_schema.s3["s3BucketName"],
                            "s3ObjectKey": action_group.api_schema.s3["s3ObjectKey"],
                        },
                    }
            elif action_group.executor == Executor.INBUILT_TOOL:
                actionGroup["parentActionGroupSignature"] = action_group.builtin_tools[
                    "parentActionGroupSignature"
                ]
                if "parentActionGroupSignatureParams" in action_group.builtin_tools:
                    actionGroup["parentActionGroupSignatureParams"] = (
                        action_group.builtin_tools["parentActionGroupSignatureParams"]
                    )

            actionGroups.append({**actionGroup})

        return actionGroups

    def __repr__(self):
        return json.dumps(self.actionGroups, indent=4)


class ActionGroupBuilder:
    @staticmethod
    def get_indent_level(line: str) -> int:
        """Count the number of leading spaces to determine indent level."""
        return len(line) - len(line.lstrip())

    @staticmethod
    def get_new_param(line: str) -> Tuple[str, List]:
        line = ActionGroupBuilder.clean_string(line.strip())
        param_parts = line.split(":", 1)
        current_param, current_desc = str(), list()
        if len(param_parts) == 2 and param_parts[1]:

            pattern = r"\((.*?)\)"
            match = re.search(pattern, param_parts[0].strip())
            current_param_type = str()
            if match:
                current_param_type = match.group(
                    1
                )  # group(1) gets just the content inside parentheses

            current_param = param_parts[0].strip().split("(")[0].strip()
            current_desc = [current_param_type + " " + param_parts[1].strip()]
        else:
            raise ValueError("Invalid docstring format")
        return current_param, current_desc

    @staticmethod
    @validate_call
    def clean_string(line: str) -> str:
        clean_line = str()
        prev_char: str = None
        for character in line:

            if character == " ":
                prev_char = " "
            else:
                if prev_char == " ":
                    clean_line += " " + character
                else:
                    clean_line += character
                prev_char = character
        return clean_line

    @staticmethod
    @validate_call
    def parse_docstring(
        docstring: Annotated[str, Field(min_length=1)],
        argument_key="Parameters:",
        return_key="Returns:",
    ) -> tuple[str, Dict[str, str]]:
        """Parse a docstring to extract function description and parameter descriptions."""
        if not docstring:
            raise ValueError("Docstring is empty or None")

        docstring = docstring.strip()
        parameter_level = None

        # Split docstring into description and args sections
        description, parameter_return_section = (None, None)
        description_parameter_return_section = docstring.split(argument_key, 1)
        # print(description_parameter_return_section)
        # Get function description
        if description_parameter_return_section:
            description = description_parameter_return_section[0].strip()
            description = description.replace("\n", " ").replace("\r", "").strip()
            description = ActionGroupBuilder.clean_string(line=description)
            # Parse parameter descriptions if they exist
            param_descriptions = {}
            if (
                len(description_parameter_return_section) > 1
                and description_parameter_return_section[1].strip()
            ):
                parameter_return_section = description_parameter_return_section[
                    1
                ].split(return_key, 1)

                if len(parameter_return_section) > 1:
                    param_section, return_section = parameter_return_section
                    return_section = return_section.strip()
                    return_section = (
                        return_section.replace("\n", " ").replace("\r", "").strip()
                    )
                    return_section = ActionGroupBuilder.clean_string(
                        line=return_section
                    )

                    description += (
                        " This function returns " + return_section
                        if return_section
                        else ""
                    )
                else:
                    param_section = parameter_return_section[0]
                # Split parameters into lines and parse each
                param_lines = param_section.split("\n")

                current_param = None
                current_desc = []
                parameter_level, current_parameter_level = 0, 0
                first_level = False
                for line in param_lines:
                    if not line or not line.strip():
                        continue

                    if not first_level:
                        parameter_level = ActionGroupBuilder.get_indent_level(line=line)
                        current_param, current_desc = ActionGroupBuilder.get_new_param(
                            line=line
                        )
                        first_level = True

                    else:
                        current_parameter_level = ActionGroupBuilder.get_indent_level(
                            line=line
                        )
                        if current_parameter_level == parameter_level:
                            if current_param:
                                param_descriptions[current_param] = " ".join(
                                    current_desc
                                ).strip()
                                current_desc = []
                            current_param, current_desc = (
                                ActionGroupBuilder.get_new_param(line=line)
                            )
                        elif current_parameter_level > parameter_level:
                            current_desc.append(
                                line.replace("\n", "").replace("\r", "").strip()
                            )
                        else:
                            raise ValueError("Invalid docstring format")
                # Save the last parameter
                if current_param:
                    param_descriptions[current_param] = " ".join(current_desc).strip()
        else:
            raise ValueError("Invalid docstring format")

        return description, param_descriptions

    @staticmethod
    @validate_call
    def _map_python_type_to_schema_type(python_type: str) -> str:
        """Map Python type names to JSON schema type names."""
        type_mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
        }

        return type_mapping.get(
            python_type, "string"
        )  # default to string for unknown types

    @staticmethod
    @validate_call
    def create_function_schema(
        func: Callable, argument_key: str = "Parameters:", return_key: str = "Returns:"
    ) -> FunctionDefination:

        if func.__doc__ is None:
            raise ValueError("Docstring is empty or None")

        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            docstring=func.__doc__, argument_key=argument_key, return_key=return_key
        )
        parameters = {}
        sig = signature(func)
        for name, param in sig.parameters.items():
            param_type_name = param.annotation
            if isinstance(param_type_name, Callable):
                param_type_name = param_type_name.__name__
            python_type = (
                param_type_name if param.annotation != Parameter.empty else "any"
            )
            schema_type = ActionGroupBuilder._map_python_type_to_schema_type(
                python_type
            )

            param_info = {
                "type": schema_type,
                "description": param_descriptions.get(name, ""),
                "required": param.default == Parameter.empty,
            }
            parameters.update({name: param_info})

        requireConfirmation = (
            "ENABLED"
            if getattr(func, "__is_confirmation_required__", False)
            else "DISABLED"
        )

        return {
            "name": func.__name__,
            "description": description,
            "parameters": parameters,
            "requireConfirmation": requireConfirmation,
        }
