import telemetry_agents


def test_package_import_exposes_version() -> None:
    assert telemetry_agents.__version__ == "0.1.0"
