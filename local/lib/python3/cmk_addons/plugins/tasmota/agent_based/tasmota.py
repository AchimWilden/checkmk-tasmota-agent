import json
import re
from collections.abc import Mapping

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Metric, Result, Service, State


def parse_tasmota(string_table):
    raw = " ".join(value for row in string_table for value in row)
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return {"error": "invalid JSON from Tasmota agent"}
    return payload if isinstance(payload, dict) else {"error": "invalid Tasmota response"}


def _numeric_values(values):
    if not isinstance(values, Mapping):
        return {}
    return {
        key: value
        for key, value in values.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _metric_name(value):
    normalized = re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")
    return normalized or "value"


def _sensors(section):
    status = section.get("StatusSNS")
    if not isinstance(status, Mapping):
        return {}
    return {
        name: _numeric_values(values)
        for name, values in status.items()
        if isinstance(values, Mapping) and _numeric_values(values)
    }


def _powers(section):
    status = section.get("StatusSTS")
    if not isinstance(status, Mapping):
        return {}
    return {
        name: value
        for name, value in status.items()
        if name.startswith("POWER") and isinstance(value, str)
    }


def discover_tasmota_device(section):
    yield Service()


def check_tasmota_device(section):
    error = section.get("error")
    if error:
        yield Result(state=State.CRIT, summary=f"Tasmota HTTP query failed: {error}")
        return

    status = section.get("StatusSTS")
    if not isinstance(status, Mapping):
        yield Result(state=State.UNKNOWN, summary="StatusSTS missing from Tasmota response")
        return

    firmware = section.get("StatusFWR", {}).get("Version", "unknown")
    uptime = status.get("UptimeSec")
    wifi = status.get("Wifi", {})
    metrics = {}
    if isinstance(uptime, (int, float)):
        metrics["uptime_seconds"] = uptime
    if isinstance(status.get("Heap"), (int, float)):
        metrics["heap_kib"] = status["Heap"]
    if isinstance(status.get("LoadAvg"), (int, float)):
        metrics["load_average"] = status["LoadAvg"]
    if isinstance(wifi, Mapping):
        if isinstance(wifi.get("RSSI"), (int, float)):
            metrics["wifi_rssi_percent"] = wifi["RSSI"]
        if isinstance(wifi.get("Signal"), (int, float)):
            metrics["wifi_signal_dbm"] = wifi["Signal"]

    for name, value in metrics.items():
        yield Metric(name=name, value=value)
    yield Result(
        state=State.OK,
        summary=f"Firmware {firmware}; {len(_sensors(section))} sensor(s); {len(_powers(section))} relay(s)",
    )


def discover_tasmota_sensors(section):
    for name in _sensors(section):
        yield Service(item=name)


def check_tasmota_sensor(item, section):
    values = _sensors(section).get(item)
    if not values:
        yield Result(state=State.UNKNOWN, summary="Sensor data missing")
        return

    summary = []
    for key, value in sorted(values.items()):
        metric_name = _metric_name(key)
        yield Metric(name=metric_name, value=value)
        summary.append(f"{key} {value:g}")
    yield Result(state=State.OK, summary="; ".join(summary))


def discover_tasmota_powers(section):
    for name in _powers(section):
        yield Service(item=name)


def check_tasmota_power(item, section):
    value = _powers(section).get(item)
    if value not in {"ON", "OFF"}:
        yield Result(state=State.UNKNOWN, summary="Relay state missing or unsupported")
        return
    yield Result(state=State.OK, summary=value)


agent_section_tasmota = AgentSection(
    name="tasmota",
    parse_function=parse_tasmota,
)

check_plugin_tasmota_device = CheckPlugin(
    name="tasmota_device",
    sections=["tasmota"],
    service_name="Tasmota Device",
    discovery_function=discover_tasmota_device,
    check_function=check_tasmota_device,
)

check_plugin_tasmota_sensor = CheckPlugin(
    name="tasmota_sensor",
    sections=["tasmota"],
    service_name="Tasmota Sensor %s",
    discovery_function=discover_tasmota_sensors,
    check_function=check_tasmota_sensor,
)

check_plugin_tasmota_power = CheckPlugin(
    name="tasmota_power",
    sections=["tasmota"],
    service_name="Tasmota Relay %s",
    discovery_function=discover_tasmota_powers,
    check_function=check_tasmota_power,
)