from typing import NamedTuple, List


class AWSInfo(NamedTuple):
    account: str
    execution_role: str
    region: str
    env: str
    security_group_ids: List[str]
    subnets: List[str]
    s3_path: str
    tf_bucket: str


class BlueGreenInfo(NamedTuple):
    route_strategy: str
    wait_interval: int
    max_exec_timeout: int
    term_wait: int

class AutoscalingInfo(NamedTuple):
    min_instance: int
    max_instance: int
    target_value: int
    scale_in_cooldown: int
    scale_out_cooldown: int


class ServerInfo(NamedTuple):
    host: str
    port: int
    n_workers: int
    dev: bool
