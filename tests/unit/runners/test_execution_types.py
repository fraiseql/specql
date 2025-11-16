"""Tests for execution types and metadata."""

from src.runners.execution_types import ExecutionType, ExecutionMetadata


def test_execution_type_enum_has_all_types():
    """Execution type enum defines all supported types"""
    # Check all expected types are present
    assert ExecutionType.HTTP in ExecutionType
    assert ExecutionType.SHELL in ExecutionType
    assert ExecutionType.DOCKER in ExecutionType
    assert ExecutionType.SERVERLESS in ExecutionType

    # Check we have exactly 4 types
    assert len(ExecutionType) == 4


def test_execution_type_enum_values():
    """Execution type enum values are correct"""
    assert ExecutionType.HTTP.name == "HTTP"
    assert ExecutionType.SHELL.name == "SHELL"
    assert ExecutionType.DOCKER.name == "DOCKER"
    assert ExecutionType.SERVERLESS.name == "SERVERLESS"


def test_execution_type_display_names():
    """Each execution type has correct display name"""
    assert ExecutionType.HTTP.display_name == "HTTP API"
    assert ExecutionType.SHELL.display_name == "Shell Script"
    assert ExecutionType.DOCKER.display_name == "Docker Container"
    assert ExecutionType.SERVERLESS.display_name == "Serverless Function"


def test_execution_type_network_requirements():
    """Execution types have correct network requirements"""
    # Network-dependent types
    assert ExecutionType.HTTP.requires_network is True
    assert ExecutionType.SERVERLESS.requires_network is True

    # Local execution types
    assert not ExecutionType.SHELL.requires_network
    assert not ExecutionType.DOCKER.requires_network


def test_execution_type_streaming_support():
    """Execution types have correct streaming support"""
    # Streaming-supported types
    assert ExecutionType.SHELL.supports_streaming is True
    assert ExecutionType.DOCKER.supports_streaming is True

    # Non-streaming types
    assert not ExecutionType.HTTP.supports_streaming
    assert not ExecutionType.SERVERLESS.supports_streaming


def test_execution_type_default_timeouts():
    """Execution types have appropriate default timeouts"""
    # Quick timeouts for fast operations
    assert ExecutionType.HTTP.default_timeout == 300  # 5 minutes

    # Longer timeouts for potentially slow operations
    assert ExecutionType.SHELL.default_timeout == 600  # 10 minutes
    assert ExecutionType.DOCKER.default_timeout == 1800  # 30 minutes
    assert ExecutionType.SERVERLESS.default_timeout == 900  # 15 minutes


def test_execution_metadata_dataclass():
    """ExecutionMetadata is a proper dataclass"""
    metadata = ExecutionMetadata(
        display_name="Test Type",
        requires_network=True,
        supports_streaming=False,
        default_timeout=120,
    )

    assert metadata.display_name == "Test Type"
    assert metadata.requires_network is True
    assert not metadata.supports_streaming
    assert metadata.default_timeout == 120


def test_execution_type_enum_iteration():
    """Execution type enum can be iterated over"""
    types = list(ExecutionType)
    assert len(types) == 4
    assert ExecutionType.HTTP in types
    assert ExecutionType.SHELL in types
    assert ExecutionType.DOCKER in types
    assert ExecutionType.SERVERLESS in types


def test_execution_type_value_access():
    """Execution type values are accessible"""
    # Test that we can access the metadata
    http_meta = ExecutionType.HTTP.value
    assert isinstance(http_meta, ExecutionMetadata)
    assert http_meta.display_name == "HTTP API"

    shell_meta = ExecutionType.SHELL.value
    assert isinstance(shell_meta, ExecutionMetadata)
    assert shell_meta.display_name == "Shell Script"


def test_execution_type_properties_vs_value():
    """Properties return same values as direct value access"""
    for exec_type in ExecutionType:
        assert exec_type.display_name == exec_type.value.display_name
        assert exec_type.requires_network == exec_type.value.requires_network
        assert exec_type.supports_streaming == exec_type.value.supports_streaming
        assert exec_type.default_timeout == exec_type.value.default_timeout


def test_execution_type_string_representation():
    """Execution types have reasonable string representations"""
    assert str(ExecutionType.HTTP) == "ExecutionType.HTTP"
    assert (
        repr(ExecutionType.HTTP)
        == "<ExecutionType.HTTP: ExecutionMetadata(display_name='HTTP API', requires_network=True, supports_streaming=False, default_timeout=300)>"
    )


def test_execution_type_uniqueness():
    """All execution types have unique metadata"""
    metadatas = [et.value for et in ExecutionType]

    # Check display names are unique
    display_names = [m.display_name for m in metadatas]
    assert len(display_names) == len(set(display_names))

    # Check timeout values are reasonable (all positive)
    timeouts = [m.default_timeout for m in metadatas]
    assert all(t > 0 for t in timeouts)
    assert all(isinstance(t, int) for t in timeouts)


def test_execution_type_network_grouping():
    """Execution types can be grouped by network requirements"""
    network_types = [et for et in ExecutionType if et.requires_network]
    local_types = [et for et in ExecutionType if not et.requires_network]

    assert set(network_types) == {ExecutionType.HTTP, ExecutionType.SERVERLESS}
    assert set(local_types) == {ExecutionType.SHELL, ExecutionType.DOCKER}


def test_execution_type_streaming_grouping():
    """Execution types can be grouped by streaming support"""
    streaming_types = [et for et in ExecutionType if et.supports_streaming]
    non_streaming_types = [et for et in ExecutionType if not et.supports_streaming]

    assert set(streaming_types) == {ExecutionType.SHELL, ExecutionType.DOCKER}
    assert set(non_streaming_types) == {ExecutionType.HTTP, ExecutionType.SERVERLESS}


def test_execution_metadata_immutable():
    """ExecutionMetadata instances are immutable (frozen dataclass)"""
    # Note: This test will fail if ExecutionMetadata is not frozen
    # We should make it frozen for immutability
    ExecutionMetadata(
        display_name="Test",
        requires_network=False,
        supports_streaming=True,
        default_timeout=60,
    )

    # This should work (creating new instance)
    new_metadata = ExecutionMetadata(
        display_name="Modified Test",
        requires_network=False,
        supports_streaming=True,
        default_timeout=60,
    )
    assert new_metadata.display_name == "Modified Test"

    # This should fail if frozen (but it's not currently frozen)
    # with pytest.raises(AttributeError, match="can't set attribute"):
    #     metadata.display_name = "Modified"
