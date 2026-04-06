from __future__ import annotations

import json
from typing import Any

from kafka import KafkaConsumer, KafkaProducer


def _serialize_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _deserialize_json(payload: bytes) -> dict[str, Any]:
    return json.loads(payload.decode("utf-8"))


def build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=_serialize_json,
        key_serializer=lambda key: key.encode("utf-8") if key else None,
        linger_ms=50,
    )


def build_consumer(
    topic: str,
    *,
    bootstrap_servers: str,
    group_id: str,
    consumer_timeout_ms: int,
) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=_deserialize_json,
        key_deserializer=lambda key: key.decode("utf-8") if key else None,
        consumer_timeout_ms=consumer_timeout_ms,
    )
