import boto3
import time

from typing import Dict, Any, List


def execute_athena_query(
    query: str,
    athena_db: str,
    athena_bucket: str,
    max_fetch_query_res_attempts: int = 10,
    fetch_query_res_interval: int = 1,
) -> List[Dict[str, Any]]:
    """Execute an Athena query and return the results."""
    athena_client = boto3.client("athena")

    query_execution = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": athena_db},
        ResultConfiguration={"OutputLocation": f"s3://{athena_bucket}/athenaoutput/"},
    )

    for _ in range(max_fetch_query_res_attempts):
        time.sleep(fetch_query_res_interval)
        execution_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution["QueryExecutionId"]
        )
        query_state = execution_status["QueryExecution"]["Status"]["State"]
        if query_state == "SUCCEEDED":
            results = athena_client.get_query_results(
                QueryExecutionId=query_execution["QueryExecutionId"]
            )
            return results["ResultSet"]["Rows"]
        elif query_state in ("FAILED", "CANCELLED"):
            raise Exception(f"Query execution failed with state: {query_state}")

    raise Exception("Query execution timed out")
