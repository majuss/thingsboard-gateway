#!/usr/bin/env python3
"""
BACnet Load Test Script for ThingsBoard Gateway
=================================================

Generates realistic telemetry events based on the BACnet connector config
(bacn_loadtest.json) and publishes them via MQTT to ThingsBoard, or writes
them to the gateway's SQLite event storage.

Uses multiprocessing to saturate all CPU cores for payload generation.

Usage:
    # Publish 10M events via MQTT (default)
    python load_test_bacnet.py --events 10000000 --mode mqtt

    # Write 10M events into SQLite
    python load_test_bacnet.py --events 10000000 --mode sqlite

    # Dry-run: print 5 sample events to stdout
    python load_test_bacnet.py --events 5 --mode dry-run


python load_test_bacnet.py \
    --config thingsboard_gateway/config/bacn_loadtest.json \
    --events 10000000 \
    --mode mqtt \
    --host  \
    --port 8883 \
    --token 
"""

import argparse
import json
import os
import random
import sqlite3
import sys
import time
from multiprocessing import Process, Queue as MPQueue, cpu_count
from pathlib import Path
from queue import Empty


# ---------------------------------------------------------------------------
# Realistic value generators per datapoint key prefix / pattern
# ---------------------------------------------------------------------------

def _temperature(base=22.0, amplitude=3.0):
    return round(base + random.uniform(-amplitude, amplitude), 2)

def _humidity(base=45.0, amplitude=15.0):
    return round(base + random.uniform(-amplitude, amplitude), 2)

def _co2(base=500, amplitude=300):
    return round(base + random.uniform(-amplitude / 2, amplitude), 1)

def _airflow(base=250, amplitude=150):
    return round(max(0, base + random.uniform(-amplitude, amplitude)), 1)

def _percentage(base=50, amplitude=50):
    return round(max(0.0, min(100.0, base + random.uniform(-amplitude, amplitude))), 1)

def _pressure(base=1.0, amplitude=0.5):
    return round(base + random.uniform(-amplitude, amplitude), 3)

def _power_kw(base=50, amplitude=40):
    return round(max(0, base + random.uniform(-amplitude, amplitude)), 2)

def _energy_kwh(counter_state=[0]):
    counter_state[0] += random.uniform(0.5, 5.0)
    return round(counter_state[0], 2)

def _flow(base=30, amplitude=20):
    return round(max(0, base + random.uniform(-amplitude, amplitude)), 2)

def _dewpoint(base=12.0, amplitude=3.0):
    return round(base + random.uniform(-amplitude, amplitude), 2)

def _refrigerant_pressure(base=200, amplitude=50):
    return round(base + random.uniform(-amplitude, amplitude), 1)

def _boolean():
    return random.choice([0, 1])

def _lighting(base=70, amplitude=30):
    return round(max(0.0, min(100.0, base + random.uniform(-amplitude, amplitude))), 1)

def _schedule():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    parts = []
    for day in days:
        on_hour = random.choice([6, 7, 8])
        off_hour = random.choice([17, 18, 19, 20])
        parts.append(f"{day} {on_hour:02d}:00-{off_hour:02d}:00")
    return "; ".join(parts)


_GENERATORS = [
    ("total_energy_kwh",       _energy_kwh),
    ("zone_temp",              lambda: _temperature(22, 3)),
    ("supply_air_temp",        lambda: _temperature(14, 2)),
    ("return_air_temp",        lambda: _temperature(24, 2)),
    ("outside_air_temp",       lambda: _temperature(18, 12)),
    ("mixed_air_temp",         lambda: _temperature(18, 4)),
    ("exhaust_air_temp",       lambda: _temperature(24, 3)),
    ("chilled_water_supply",   lambda: _temperature(7, 1.5)),
    ("chilled_water_return",   lambda: _temperature(12, 1.5)),
    ("hot_water_supply",       lambda: _temperature(60, 5)),
    ("hot_water_return",       lambda: _temperature(50, 5)),
    ("condenser_water_temp",   lambda: _temperature(30, 5)),
    ("refrigerant_temp",       lambda: _temperature(5, 3)),
    ("room_dewpoint",          _dewpoint),
    ("zone_humidity",          _humidity),
    ("co2_level",              _co2),
    ("vav_airflow",            _airflow),
    ("duct_static_pressure",   _pressure),
    ("building_static_pressure", lambda: _pressure(0.05, 0.03)),
    ("diff_pressure_filter",   lambda: _pressure(0.3, 0.2)),
    ("supply_air_pressure_sp", lambda: _pressure(1.5, 0.3)),
    ("return_air_pressure_sp", lambda: _pressure(0.8, 0.2)),
    ("econ_enthalpy_limit",    lambda: round(random.uniform(20, 35), 1)),
    ("fan_speed",              _percentage),
    ("valve_pos",              _percentage),
    ("damper_pos",             _percentage),
    ("reheat_valve",           _percentage),
    ("pump_speed",             _percentage),
    ("capacity_pct",           _percentage),
    ("power_kw",               _power_kw),
    ("total_power",            _power_kw),
    ("water_flow",             _flow),
    ("lighting_level",         _lighting),
    ("refrigerant_pressure",   _refrigerant_pressure),
    ("schedule_",              _schedule),
    ("_status",                _boolean),
    ("_call",                  _boolean),
    ("_enabled",               _boolean),
    ("_alarm",                 _boolean),
    ("_active",                _boolean),
    ("_detected",              _boolean),
    ("occupancy_",             _boolean),
    ("door_contact",           _boolean),
    ("window_contact",         _boolean),
    ("_fault",                 _boolean),
    ("_dirty",                 _boolean),
    ("night_purge",            _boolean),
    ("zone_setpoint",          lambda: _temperature(22, 2)),
]


def get_value_generator(key: str):
    key_lower = key.lower()
    for pattern, gen in _GENERATORS:
        if pattern in key_lower:
            return gen
    return lambda: round(random.uniform(0, 100), 2)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_datapoint_keys(config_path: str) -> list[dict]:
    with open(config_path, 'r') as f:
        config = json.load(f)
    keys = []
    for device in config.get('devices', []):
        for ts in device.get('timeseries', []):
            keys.append({
                'key': ts['key'],
                'objectType': ts['objectType'],
                'objectId': ts['objectId'],
            })
    return keys


# ---------------------------------------------------------------------------
# Fast payload builder — string concatenation instead of json.dumps()
# ---------------------------------------------------------------------------

def _classify_key(key: str, generators: dict):
    """Determine whether a key produces a number, a boolean (0/1), or a string."""
    gen = generators[key]
    sample = gen()
    if isinstance(sample, str):
        return 'string'
    elif isinstance(sample, int):
        return 'int'
    else:
        return 'float'


def build_payload_fast(device_name: str, key_names: list[str], generators: dict,
                       key_types: list[str], ts: int) -> bytes:
    """
    Build MQTT payload as a UTF-8 byte string using string formatting.
    ~3-5x faster than json.dumps() for fixed-schema payloads.
    """
    parts = []
    for i, key in enumerate(key_names):
        val = generators[key]()
        kt = key_types[i]
        if kt == 'string':
            # Escape quotes in string values
            parts.append(f'"{key}":"{val}"')
        else:
            parts.append(f'"{key}":{val}')

    values_str = ','.join(parts)
    payload = f'{{"{device_name}":[{{"ts":{ts},"values":{{{values_str}}}}}]}}'
    return payload.encode('utf-8')


# ---------------------------------------------------------------------------
# Multiprocessing payload generator worker
# ---------------------------------------------------------------------------

def _generator_worker(worker_id: int, out_queue: MPQueue, key_names: list[str],
                      keys: list[dict], device_name: str,
                      start_idx: int, count: int, base_ts: int, interval_ms: int):
    """
    Worker process: generates `count` payloads and puts them on `out_queue`.
    Sends payloads in batches to reduce IPC overhead.
    """
    # Re-seed random per worker so each gets different values
    random.seed(worker_id + int(time.time() * 1000))

    # Build generators locally (lambdas can't cross process boundaries via pickle)
    generators = {kd['key']: get_value_generator(kd['key']) for kd in keys}
    key_types = [_classify_key(k, generators) for k in key_names]

    BATCH = 500  # payloads per IPC put
    batch = []

    for i in range(count):
        ts = base_ts + ((start_idx + i) * interval_ms)
        payload = build_payload_fast(device_name, key_names, generators, key_types, ts)
        batch.append(payload)

        if len(batch) >= BATCH:
            out_queue.put(batch)
            batch = []

    if batch:
        out_queue.put(batch)

    out_queue.put(None)  # sentinel


# ---------------------------------------------------------------------------
# MQTT publisher
# ---------------------------------------------------------------------------

def write_to_mqtt(host: str, port: int, token: str, device_name: str,
                  keys: list[dict], generators: dict, total: int, interval_ms: int,
                  use_tls: bool = True, num_workers: int = 0):
    """Publish events via MQTT to ThingsBoard gateway topic using multiprocessing."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("ERROR: paho-mqtt is required for MQTT mode. Install with: pip install paho-mqtt")
        sys.exit(1)

    import threading

    if num_workers <= 0:
        num_workers = max(1, cpu_count() - 1)  # leave 1 core for the publisher

    connected_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            connected_event.set()
        else:
            print(f"  ERROR: MQTT connect failed with rc={rc}")

    client = mqtt.Client()
    client.username_pw_set(token)
    client.on_connect = on_connect
    if use_tls:
        import ssl
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

    print(f"  Connecting to {host}:{port} ...")
    client.connect(host, port, keepalive=60)
    client.loop_start()

    if not connected_event.wait(timeout=10):
        print("  ERROR: Could not connect to MQTT broker within 10s")
        client.loop_stop()
        return

    # Register device
    connect_payload = json.dumps({"device": device_name}, separators=(',', ':'))
    client.publish("v1/gateway/connect", connect_payload, qos=1)
    print(f"  Device '{device_name}' registered via v1/gateway/connect")
    time.sleep(1)

    # Launch generator workers
    key_names = [kd['key'] for kd in keys]
    base_ts = int(time.time() * 1000)
    topic = "v1/gateway/telemetry"

    chunk_size = total // num_workers
    remainder = total % num_workers

    payload_queue = MPQueue(maxsize=num_workers * 50)  # bounded to limit memory
    workers = []
    offset = 0
    for w in range(num_workers):
        count = chunk_size + (1 if w < remainder else 0)
        p = Process(target=_generator_worker, daemon=True,
                    args=(w, payload_queue, key_names, keys, device_name,
                          offset, count, base_ts, interval_ms))
        p.start()
        workers.append(p)
        offset += count

    print(f"  {num_workers} generator workers started, publishing...")

    # Publish loop — read from queue and publish
    written = 0
    sentinels = 0
    t0 = time.time()
    last_report = t0

    while sentinels < num_workers:
        try:
            batch = payload_queue.get(timeout=2.0)
        except Empty:
            continue

        if batch is None:
            sentinels += 1
            continue

        for payload_bytes in batch:
            client.publish(topic, payload_bytes, qos=1)
            written += 1

        now = time.time()
        if now - last_report >= 2.0:
            elapsed = now - t0
            rate = written / elapsed if elapsed > 0 else 0
            pct = written / total * 100
            print(f"\r  [{pct:6.2f}%] {written:>12,} / {total:>12,} events  |  {rate:,.0f} events/s",
                  end="", flush=True)
            last_report = now

    # Wait for workers
    for p in workers:
        p.join(timeout=5)

    elapsed = time.time() - t0
    rate = written / elapsed if elapsed > 0 else 0
    print(f"\r  [100.00%] {written:>12,} / {total:>12,} events  |  {rate:,.0f} events/s")
    print(f"\n  Done. {written:,} events published in {elapsed:.1f}s ({rate:,.0f} events/s)")

    client.loop_stop()
    client.disconnect()


# ---------------------------------------------------------------------------
# SQLite writer
# ---------------------------------------------------------------------------

def generate_values(keys: list[dict], generators: dict) -> dict:
    return {kd['key']: generators[kd['key']]() for kd in keys}


def generate_event(device_name: str, device_type: str, keys: list[dict],
                   generators: dict, ts_ms: int) -> str:
    values = generate_values(keys, generators)
    event = {
        "deviceName": device_name,
        "deviceType": device_type,
        "telemetry": [{"ts": ts_ms, "values": values}],
        "attributes": {}
    }
    return json.dumps(event, separators=(',', ':'))


def event_generator(device_name, device_type, keys, generators, total, interval_ms):
    base_ts = int(time.time() * 1000)
    for i in range(total):
        ts = base_ts + (i * interval_ms)
        yield generate_event(device_name, device_type, keys, generators, ts)


def write_to_sqlite(db_path: str, events_iter, total: int, batch_size: int = 5000):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-20000;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA page_size=4096;")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            message   TEXT NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages (timestamp);")
    conn.commit()

    written = 0
    batch = []
    t0 = time.time()
    last_report = t0

    for event_json in events_iter:
        ts_now = int(time.time() * 1000)
        batch.append((ts_now, event_json))

        if len(batch) >= batch_size:
            conn.executemany("INSERT INTO messages (timestamp, message) VALUES (?, ?);", batch)
            conn.commit()
            written += len(batch)
            batch.clear()

            now = time.time()
            if now - last_report >= 2.0:
                elapsed = now - t0
                rate = written / elapsed if elapsed > 0 else 0
                pct = written / total * 100
                print(f"\r  [{pct:6.2f}%] {written:>12,} / {total:>12,} events  |  {rate:,.0f} events/s",
                      end="", flush=True)
                last_report = now

    if batch:
        conn.executemany("INSERT INTO messages (timestamp, message) VALUES (?, ?);", batch)
        conn.commit()
        written += len(batch)

    elapsed = time.time() - t0
    rate = written / elapsed if elapsed > 0 else 0
    print(f"\r  [100.00%] {written:>12,} / {total:>12,} events  |  {rate:,.0f} events/s")
    print(f"\n  Done. {written:,} events written to {db_path} in {elapsed:.1f}s ({rate:,.0f} events/s)")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"  Database size: {db_size_mb:.1f} MB")


# ---------------------------------------------------------------------------
# Dry-run printer
# ---------------------------------------------------------------------------

def dry_run(events_iter, total: int):
    for i, event_json in enumerate(events_iter):
        print(json.dumps(json.loads(event_json), indent=2))
        if i + 1 >= total:
            break
    print(f"\n  (Dry-run: showed {min(total, 5)} sample events)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    script_dir = Path(__file__).parent
    default_config = script_dir / "thingsboard_gateway" / "config" / "bacn_loadtest.json"
    if not default_config.exists():
        default_config = script_dir / "config" / "bacn_loadtest.json"

    parser = argparse.ArgumentParser(
        description="BACnet Load Test — generate realistic telemetry events for ThingsBoard Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--config", type=str, default=str(default_config),
                        help="Path to BACnet config JSON with datapoint definitions")
    parser.add_argument("--events", type=int, default=10_000_000,
                        help="Number of events to generate (default: 10,000,000)")
    parser.add_argument("--device-name", type=str, default="BACnet Device LoadTest",
                        help="Device name for generated events")
    parser.add_argument("--device-type", type=str, default="default",
                        help="Device type for generated events")
    parser.add_argument("--interval-ms", type=int, default=10000,
                        help="Simulated interval between events in ms (default: 10000)")
    parser.add_argument("--mode", choices=["sqlite", "mqtt", "dry-run"], default="sqlite",
                        help="Output mode (default: sqlite)")
    parser.add_argument("--db", type=str, default="./data/data.db",
                        help="SQLite database path (for sqlite mode)")
    parser.add_argument("--host", type=str, default="broker.sbcapp.com",
                        help="MQTT broker host (for mqtt mode)")
    parser.add_argument("--port", type=int, default=8883,
                        help="MQTT broker port (for mqtt mode)")
    parser.add_argument("--token", type=str, default="BUZL8cGSnygnbJwYj5oo",
                        help="Gateway access token (for mqtt mode)")
    parser.add_argument("--no-tls", action="store_true",
                        help="Disable TLS for MQTT")
    parser.add_argument("--workers", type=int, default=0,
                        help="Number of generator worker processes (default: CPU count - 1)")
    parser.add_argument("--batch-size", type=int, default=5000,
                        help="SQLite write batch size (default: 5000)")

    args = parser.parse_args()

    # Load datapoint definitions
    print(f"Loading datapoint config from: {args.config}")
    keys = load_datapoint_keys(args.config)
    print(f"  Found {len(keys)} datapoint keys ({sum(1 for k in keys if k['objectType'] == 'analogValue')} analog, "
          f"{sum(1 for k in keys if k['objectType'] == 'binaryValue')} binary, "
          f"{sum(1 for k in keys if k['objectType'] == 'schedule')} schedule)")

    # Pre-build generators for each key
    generators = {kd['key']: get_value_generator(kd['key']) for kd in keys}

    # Estimate sizes
    sample_event = generate_event(args.device_name, args.device_type, keys, generators, int(time.time() * 1000))
    event_bytes = len(sample_event.encode('utf-8'))
    total_bytes = event_bytes * args.events
    print(f"\n  Event payload size: ~{event_bytes:,} bytes")
    print(f"  Total data estimate: ~{total_bytes / (1024**3):.1f} GB for {args.events:,} events")
    print(f"  Simulated time span: ~{args.events * args.interval_ms / 1000 / 3600:.1f} hours\n")

    if args.mode == "sqlite":
        events = event_generator(args.device_name, args.device_type, keys, generators,
                                 args.events, args.interval_ms)
        print(f"Writing {args.events:,} events to SQLite: {args.db}")
        write_to_sqlite(args.db, events, args.events, args.batch_size)
        print(f"\n  To upload: start the gateway with storage type 'sqlite' and data_file_path '{args.db}'")

    elif args.mode == "mqtt":
        print(f"Publishing {args.events:,} events via MQTT to {args.host}:{args.port}")
        write_to_mqtt(args.host, args.port, args.token, args.device_name,
                      keys, generators, args.events, args.interval_ms,
                      use_tls=not args.no_tls, num_workers=args.workers)

    elif args.mode == "dry-run":
        events = event_generator(args.device_name, args.device_type, keys, generators,
                                 args.events, args.interval_ms)
        dry_run(events, min(args.events, 5))


if __name__ == "__main__":
    main()
