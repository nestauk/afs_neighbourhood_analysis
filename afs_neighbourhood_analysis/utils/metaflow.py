from metaflow import Flow, Run
from metaflow.exception import MetaflowNotFound


def get_run(flow_name: str) -> Run:
    """Last successful run of `flow_name` executed with `--production`."""
    runs = Flow(flow_name).runs("project_branch:prod")
    try:
        return next(filter(lambda run: run.successful, runs))
    except StopIteration as exc:
        raise MetaflowNotFound("Matching run not found") from exc
