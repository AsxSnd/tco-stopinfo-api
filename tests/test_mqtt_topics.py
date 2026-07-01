from tco_stopinfo.config import MqttConfig
from tco_stopinfo.mqtt_client import parse_mqtt_topic


def test_nested_vilnius_topic_layout() -> None:
    cfg = MqttConfig(root="vilniustest", topic_prefix="pis", pis_instance="0")

    assert parse_mqtt_topic("vilniustest/1232/pis/0/journey", cfg) == ("1232", "journey")
    assert parse_mqtt_topic("vilniustest/1232/pis/0/list/stops", cfg) == ("1232", "list/stops")
    assert parse_mqtt_topic("vilniustest/1232/pis/0/stopinfo", cfg) == ("1232", "stopinfo")
    assert parse_mqtt_topic("pis/1232/journey", cfg) is None
    assert parse_mqtt_topic("vilniustest/1232/pis/1/journey", cfg) is None


def test_flat_legacy_topic_layout() -> None:
    cfg = MqttConfig(root="", topic_prefix="pis")

    assert parse_mqtt_topic("pis/1232/journey", cfg) == ("1232", "journey")
    assert parse_mqtt_topic("vilniustest/1232/pis/0/journey", cfg) is None


def test_subscription_patterns() -> None:
    cfg = MqttConfig(root="vilniustest", topic_prefix="pis", pis_instance="0")
    assert cfg.subscription_topic("journey") == "vilniustest/+/pis/0/journey"
    assert cfg.describe_layout() == "vilniustest/{vehicle}/pis/0/{suffix}"
