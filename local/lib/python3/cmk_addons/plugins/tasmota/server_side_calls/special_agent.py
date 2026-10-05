from cmk.server_side_calls.v1 import (
    SpecialAgentCommand,
    SpecialAgentConfig,
    noop_parser,
)


def _agent_arguments(params, host_config):
    address = host_config.primary_ip_config.address or host_config.name
    yield SpecialAgentCommand(
        command_arguments=[
            "--address",
            address,
            "--port",
            str(params["port"]),
            "--timeout",
            str(params["timeout"]),
        ]
    )


special_agent_tasmota = SpecialAgentConfig(
    name="tasmota",
    parameter_parser=noop_parser,
    commands_function=_agent_arguments,
)