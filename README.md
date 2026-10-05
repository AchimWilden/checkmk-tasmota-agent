# Checkmk Tasmota Special Agent

The Checkmk 2.4 special agent polls `Status 0` over HTTP for hosts assigned the
Tasmota host tag. It uses the host's primary IP address, sends the `Referer`
header required by Tasmota, and discovers device, numeric sensor, and relay
services from the response. The agent has no dependency on a particular host
tag group or tag ID.

## Install

Copy `local/lib/python3/cmk_addons/plugins/tasmota` into the same path below the
Checkmk site's `local` directory. Preserve the executable bit on
`libexec/agent_tasmota`. Then run `cmk-validate-plugins` as the site user and
restart the site web server so the rule appears in Setup.

## Configure the trigger

1. Set each Tasmota host's primary IP address to the device address.
2. Set the host's built-in `Checkmk agent / API integrations` tag to either
   `Configured API integrations and Checkmk agent` or
   `Configured API integrations, no Checkmk agent`.
3. Add a rule for `Tasmota via HTTP` under Setup > Agents > Other integrations.
4. In the rule conditions, select the host tag group and value used to identify
   Tasmota devices in your Checkmk installation. Set the HTTP port and timeout
   as needed.
5. Activate changes, then run service discovery on the matching hosts.

Checkmk runs the special agent at its normal check interval only for hosts
matching the rule. New sensor and relay services are found during service
discovery. Sensor values are exported as metrics; relay states are informational
and do not assume that a relay must be on or off.

The HTTP API must be reachable from the Checkmk site. This initial version
supports unauthenticated HTTP and does not use the cumulative `MqttCount` as a
live MQTT connection indicator.