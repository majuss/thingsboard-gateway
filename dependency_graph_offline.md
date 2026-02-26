# ThingsBoard Gateway Dependency Graph (Offline Analysis)

Generated from local source + installed metadata (no internet access).

## Python Floor

- Project `python_requires`: `>=3.10` (from `setup.py`).
- Max package floor among locally-resolved graph: `3.10.0`.
- Some optional connector packages are not installed locally, so their exact `Requires-Python` is unknown in this offline run.

## Connector Runtime Install Triggers

| Package | Version arg in code | Trigger locations | Installed locally |
|---|---|---|---|
| `aiohttp` | `upgrade` | `thingsboard_gateway/connectors/rest/rest_connector.py:49` | no |
| `asyncua` | `required_version` | `thingsboard_gateway/connectors/opcua/opcua_connector.py:59` | no |
| `bacpypes3` | `upgrade` | `thingsboard_gateway/connectors/bacnet/bacnet_connector.py:49` | yes |
| `bleak` | `upgrade` | `thingsboard_gateway/connectors/ble/ble_connector.py:35` | no |
| `cryptography` | `upgrade` | `thingsboard_gateway/connectors/rest/ssl_generator.py:13`, `thingsboard_gateway/grpc_connectors/opcua/opcua_connector.py:43` | yes |
| `debugpy` | `upgrade` | `thingsboard_gateway/tb_gateway.py:67` | no |
| `ocpp` | `upgrade` | `thingsboard_gateway/connectors/ocpp/ocpp_connector.py:38` | no |
| `opcua` | `upgrade` | `thingsboard_gateway/grpc_connectors/opcua/opcua_connector.py:37` | no |
| `paho-mqtt` | `>=1.6; upgrade` | `thingsboard_gateway/connectors/mqtt/mqtt_connector.py:45`, `thingsboard_gateway/grpc_connectors/mqtt/mqtt_connector.py:36` | no |
| `puresnmp` | `>=2.0.0` | `thingsboard_gateway/connectors/snmp/snmp_connector.py:43` | no |
| `pymodbus` | `3.0.0; required_version` | `thingsboard_gateway/connectors/modbus/modbus_connector.py:57`, `thingsboard_gateway/grpc_connectors/modbus/modbus_connector.py:48` | no |
| `pyodbc` | `upgrade` | `thingsboard_gateway/connectors/odbc/odbc_connector.py:38` | no |
| `pyserial` | `upgrade` | `thingsboard_gateway/connectors/modbus/modbus_connector.py:58`, `thingsboard_gateway/extensions/serial/custom_serial_connector.py:29`, `thingsboard_gateway/grpc_connectors/modbus/modbus_connector.py:49` | no |
| `pyserial-asyncio` | `upgrade` | `thingsboard_gateway/connectors/modbus/modbus_connector.py:59`, `thingsboard_gateway/grpc_connectors/modbus/modbus_connector.py:50` | no |
| `python-can` | `upgrade` | `thingsboard_gateway/connectors/can/can_connector.py:33` | no |
| `requests` | `upgrade` | `thingsboard_gateway/connectors/request/request_connector.py:32`, `thingsboard_gateway/connectors/rest/rest_connector.py:42` | yes |
| `slixmpp` | `upgrade` | `thingsboard_gateway/connectors/xmpp/xmpp_connector.py:36` | no |
| `tb-mqtt-client` | `upgrade` | `thingsboard_gateway/gateway/tb_client.py:52` | yes |
| `thingsboard-gateway` | `self.__version["latest_version"]` | `thingsboard_gateway/tb_utility/tb_updater.py:113` | yes |
| `twisted` | `upgrade` | `thingsboard_gateway/grpc_connectors/modbus/modbus_connector.py:55` | no |
| `websockets` | `upgrade` | `thingsboard_gateway/connectors/ocpp/ocpp_connector.py:45` | no |
| `xknx` | `upgrade` | `thingsboard_gateway/connectors/knx/knx_connector.py:33` | no |

## Declared Requirements

### Base (`requirements.txt`)

- `cachetools`
- `cryptography`
- `grpcio`
- `jsonpath-rw`
- `mmh3`
- `orjson`
- `packaging==23.1`
- `pip`
- `protobuf`
- `psutil`
- `pybase64`
- `PySocks`
- `python-dateutil`
- `PyYAML`
- `regex`
- `requests>=2.32.3`
- `service-identity`
- `setuptools`
- `simplejson`
- `tb-mqtt-client==1.13.13`
- `tb-paho-mqtt-client>=2.1.2`
- `urllib3>=2.3.0`

### Full (`requirements-full.txt`)

- `aiohttp`
- `asyncua==1.1.5`
- `bacpypes3`
- `bleak`
- `cachetools`
- `cryptography`
- `grpcio`
- `jsonpath-rw`
- `mmh3`
- `ocpp`
- `orjson`
- `packaging==23.1`
- `paho-mqtt`
- `pip`
- `protobuf`
- `psutil`
- `puresnmp>=2.0.0`
- `pybase64`
- `pymodbus==3.9.2`
- `pyodbc`
- `pyserial`
- `pyserial-asyncio`
- `PySocks`
- `python-can`
- `python-dateutil`
- `PyYAML`
- `regex`
- `requests`
- `service-identity`
- `setuptools`
- `simplejson`
- `slixmpp`
- `tb-mqtt-client==1.13.13`
- `tb-paho-mqtt-client>=2.1.2`
- `urllib3>=2.3.0`
- `wheel`
- `xknx`

## Resolved Graph (Installed Packages)

| Package | Version | Requires-Python | Min Python | Direct dependencies (active markers only) |
|---|---|---|---|---|
| `attrs` | `25.3.0` | `>=3.8` | `3.8.0` | — |
| `bacpypes3` | `0.0.104` | `>=3.8` | `3.8.0` | — |
| `cachetools` | `5.5.2` | `>=3.7` | `3.7.0` | — |
| `certifi` | `2025.1.31` | `>=3.6` | `3.6.0` | — |
| `cffi` | `1.17.1` | `>=3.8` | `3.8.0` | `pycparser*` |
| `charset-normalizer` | `3.4.1` | `>=3.7` | `3.7.0` | — |
| `cryptography` | `44.0.2` | `>=3.7, !=3.9.0, !=3.9.1` | `3.7.0` | `cffi>=1.12` |
| `decorator` | `5.2.1` | `>=3.8` | `3.8.0` | — |
| `grpcio` | `1.71.0` | `>=3.9` | `3.9.0` | — |
| `idna` | `3.10` | `>=3.6` | `3.6.0` | — |
| `jsonpath-rw` | `1.4.0` | `` | `` | `ply*`, `decorator*`, `six*` |
| `mmh3` | `5.1.0` | `>=3.9` | `3.9.0` | — |
| `orjson` | `3.10.16` | `>=3.9` | `3.9.0` | — |
| `packaging` | `23.1` | `>=3.7` | `3.7.0` | — |
| `pip` | `25.0.1` | `>=3.8` | `3.8.0` | — |
| `ply` | `3.11` | `` | `` | — |
| `protobuf` | `3.20.0` | `>=3.7` | `3.7.0` | — |
| `psutil` | `7.0.0` | `>=3.6` | `3.6.0` | — |
| `pyasn1` | `0.6.1` | `>=3.8` | `3.8.0` | — |
| `pyasn1-modules` | `0.4.2` | `>=3.8` | `3.8.0` | `pyasn1<0.7.0,>=0.6.1` |
| `pybase64` | `1.4.1` | `>=3.8` | `3.8.0` | — |
| `pycparser` | `2.22` | `>=3.8` | `3.8.0` | — |
| `pysocks` | `1.7.1` | `>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*` | `3.4.0` | — |
| `python-dateutil` | `2.9.0.post0` | `!=3.0.*,!=3.1.*,!=3.2.*,>=2.7` | `3.3.0` | `six>=1.5` |
| `pyyaml` | `6.0.2` | `>=3.8` | `3.8.0` | — |
| `regex` | `2024.11.6` | `>=3.8` | `3.8.0` | — |
| `requests` | `2.32.3` | `>=3.8` | `3.8.0` | `charset-normalizer<4,>=2`, `idna<4,>=2.5`, `urllib3<3,>=1.21.1`, `certifi>=2017.4.17` |
| `service-identity` | `24.2.0` | `>=3.8` | `3.8.0` | `attrs>=19.1.0`, `cryptography*`, `pyasn1*`, `pyasn1-modules*` |
| `setuptools` | `78.1.0` | `>=3.9` | `3.9.0` | — |
| `simplejson` | `3.20.1` | `>=2.5, !=3.0.*, !=3.1.*, !=3.2.*` | `3.3.0` | — |
| `six` | `1.17.0` | `>=2.7, !=3.0.*, !=3.1.*, !=3.2.*` | `3.3.0` | — |
| `tb-mqtt-client` | `1.13.12` | `>=3.9` | `3.9.0` | `tb-paho-mqtt-client>=2.1.2`, `requests>=2.31.0`, `orjson*` |
| `tb-paho-mqtt-client` | `2.1.2` | `>=3.7` | `3.7.0` | — |
| `thingsboard-gateway` | `3.8.2` | `>=3.10` | `3.10.0` | `setuptools<82.0.0`, `cryptography*`, `jsonpath-rw*`, `regex*`, `pip*`, `pyyaml*`, `orjson*`, `pybase64*`, `simplejson*`, `urllib3>=2.3.0`, `requests>=2.32.3`, `mmh3*`, `grpcio*`, `protobuf*`, `python-dateutil*`, `cachetools*`, `tb-paho-mqtt-client>=2.1.2`, `tb-mqtt-client==1.13.12`, `packaging==23.1`, `service-identity*`, `psutil*`, `pysocks*` |
| `urllib3` | `2.4.0` | `>=3.9` | `3.9.0` | — |

## Unresolved (Not Installed Locally)

### Runtime-Triggered Packages Missing Locally

- `aiohttp`
- `asyncua`
- `bleak`
- `debugpy`
- `ocpp`
- `opcua`
- `paho-mqtt`
- `puresnmp`
- `pymodbus`
- `pyodbc`
- `pyserial`
- `pyserial-asyncio`
- `python-can`
- `slixmpp`
- `twisted`
- `websockets`
- `xknx`

### Declared in `requirements-full.txt` but Missing Locally

- `aiohttp`
- `asyncua`
- `bleak`
- `ocpp`
- `paho-mqtt`
- `puresnmp`
- `pymodbus`
- `pyodbc`
- `pyserial`
- `pyserial-asyncio`
- `python-can`
- `slixmpp`
- `wheel`
- `xknx`

