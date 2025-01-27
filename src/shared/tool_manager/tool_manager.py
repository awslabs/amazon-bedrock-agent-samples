#!/usr/bin/env python3
import boto3
import click
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils.bedrock_agent import Toolbox


@click.group()
@click.option('--table-name', required=False, default=Toolbox.DEFAULT_TABLE_NAME, help='DynamoDB table name')
@click.option('--region', default='us-west-2', help='AWS region')
def cli(table_name, region):
    """Tool Manager - manages lambda tools for use with (potentially many) Bedrock Agents"""
    ctx = click.get_current_context()
    # If region isn't specified, get the current region from boto3
    if region is None:
        region = boto3.Session().region_name
    ctx.obj['region'] = region
    ctx.obj['table_name'] = table_name
    ctx.obj['account'] = boto3.client("sts").get_caller_identity()["Account"]


@cli.command()
@click.pass_context
def create_table(ctx):
    """Create DynamoDB table for storing tool registration (default: bedrock_agent_tools)"""
    Toolbox.create_table(ctx.obj['table_name'])
    click.echo(f"Table created successfully")


@cli.command()
@click.pass_context
def delete_table(ctx):
    """Delete DynamoDB table for tools"""
    Toolbox.delete_table(ctx.obj['table_name'])
    click.echo(f"Table deleted successfully")


@cli.command()
@click.argument('source', type=click.Path(exists=True))
@click.pass_context
def register(ctx, source):
    """Register tools from a source definition file"""
    try:
        with open(source) as f:
            tool_source = json.load(f)

        # Validate required fields
        if 'code' not in tool_source:
            raise ValueError("Source file must contain 'code' field")
        if 'definition' not in tool_source or not isinstance(tool_source['definition'], list):
            raise ValueError("Source file must contain 'definition' field as a list")

        # For each tool definition in the source file
        for tool_def in tool_source['definition']:
            if 'name' not in tool_def:
                raise ValueError("Each tool definition must contain a 'name' field")

            # replace {region} and {account} in the code field
            tool_source['code'] = tool_source['code'].replace('{region}', ctx.obj['region'])
            tool_source['code'] = tool_source['code'].replace('{account_id}', ctx.obj['account'])

            # Register individual tool
            Toolbox.register_tool(
                tool_name=tool_def['name'],
                tool_code_or_arn=tool_source['code'],
                tool_definition=tool_def.get('parameters', ''),
                description=tool_def.get('description', '')
            )
            click.echo(f"Tool '{tool_def['name']}' registered successfully")

    except json.JSONDecodeError as e:
        click.echo(f"Error parsing source file: {str(e)}", err=True)
    except ValueError as e:
        click.echo(f"Invalid source file format: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Error registering tools: {str(e)}", err=True)


@cli.command()
@click.pass_context
def list_tools(ctx):
    """List all registered tools"""
    tools = Toolbox.list_tools(ctx.obj['table_name'])
    for tool in tools:
        click.echo(f"\nTool: {tool['tool_name']}")
        click.echo(f"Description: {tool['description']}")
        click.echo(f"Code: {tool['tool_code']}")


@cli.command()
@click.argument('name')
@click.pass_context
def unregister(ctx, name):
    """Unregister a specific tool"""
    # Check if the tool exists
    tool = Toolbox.get_tool(name, ctx.obj['table_name'])
    if not tool:
        click.echo(f"Tool '{name}' not found")
        return
    # Delete the tool from the Toolbox
    Toolbox.unregister_tool(name, ctx.obj['table_name'])
    print(f"Tool {name} unregistered from toolbox")


@cli.command()
@click.argument('name')
@click.pass_context
def get(ctx, name):
    """Get details for a specific tool"""
    tool = Toolbox.get_tool(name, ctx.obj['table_name'])
    if tool:
        click.echo(json.dumps(tool, indent=2))
    else:
        click.echo(f"Tool '{name}' not found")


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
