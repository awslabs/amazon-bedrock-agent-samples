import json
from typing import List, Tuple

from pydantic import validate_call
from InlineAgent.constants import TraceColor
from termcolor import colored


def json_safe(obj):
    """Convert object to JSON-safe format, handling complex types."""
    if isinstance(obj, dict) or isinstance(obj, list):
        return json.dumps(obj)
    return obj


@validate_call
def get_agent_from_caller_chain(caller_chain: list, index: int) -> Tuple[str, str]:

    alias_id = caller_chain[index]["agentAliasArn"]

    return get_agent_id_aliasid(alias_id)


def get_agent_id_aliasid(arn: str):
    trace_id = arn.split("agent-alias/")[1].replace("/", ":")
    agent_id, agent_alias_id = trace_id.split(":")

    return agent_id, agent_alias_id


def add_citation(citations: List, cite=1) -> str:

    agent_answer = str()

    cite_output = list()
    for citation in citations:
        text = citation["generatedResponsePart"]["textResponsePart"]["text"]
        retrievedReferences = str()
        uri = None

        for idx, retrievedReference in enumerate(citation["retrievedReferences"]):

            uri = retrievedReference["location"]["s3Location"]["uri"]
            kb_id = retrievedReference["metadata"]["x-amz-bedrock-kb-data-source-id"]

            if "content" in retrievedReference:
                if retrievedReference["content"]["type"] == "TEXT":
                    retrievedReferences += (
                        f"[{idx + 1}] " + retrievedReference["content"]["text"] + "\n"
                    )
                elif retrievedReference["content"]["type"] == "IMAGE":
                    retrievedReferences += f"[{idx + 1}] " + "Image is retrieved" + "\n"
                elif retrievedReference["content"]["type"] == "ROW":
                    retrievedReferences += (
                        f"[{idx + 1}] "
                        + " ".join(
                            [
                                f"column: {row['columnName']} value: {row['columnValue']}"
                                for row in retrievedReference["content"]["row"]
                            ]
                        )
                        + "\n"
                    )

        cite_output.append(
            (f"[{cite}] S3 URI: {uri}\nKB ID: {kb_id}", retrievedReferences)
        )

        agent_answer += text

        print(colored(f"\n\n<-- Response with Citation -->", TraceColor.cite))
        print(colored(text, TraceColor.final_output), end="")
        if citation["retrievedReferences"]:
            print(colored(f" [{cite}]", TraceColor.error), end="")

        cite += 1

    print("\n\n")
    for output in cite_output:
        if len(output[1]):
            print(colored(output[0], TraceColor.cite))
            print(colored(output[1] + "\n", TraceColor.retrieved_references))

    return agent_answer, cite
