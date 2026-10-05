from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import DefaultValue, DictElement, Dictionary, Integer
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _parameter_form():
    return Dictionary(
        title=Title("Tasmota HTTP API"),
        help_text=Help("Polls the Tasmota Status 0 endpoint for matching hosts."),
        elements={
            "port": DictElement(
                parameter_form=Integer(
                    title=Title("HTTP port"),
                    prefill=DefaultValue(80),
                    min_value=1,
                    max_value=65535,
                ),
                required=True,
            ),
            "timeout": DictElement(
                parameter_form=Integer(
                    title=Title("Request timeout in seconds"),
                    prefill=DefaultValue(5),
                    min_value=1,
                    max_value=60,
                ),
                required=True,
            ),
        },
    )


rule_spec_tasmota = SpecialAgent(
    name="tasmota",
    title=Title("Tasmota via HTTP"),
    topic=Topic.PERIPHERALS,
    parameter_form=_parameter_form,
)