"""UUID generator for SpecQL test data with encoded components"""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class UUIDComponents:
    """Decoded UUID components"""

    entity_code: str  # "012321"
    test_type: str  # "21"
    function_num: str  # "0000"
    scenario: int  # 1000
    test_case: int  # 0
    instance: int  # 1

    def __str__(self) -> str:
        return (
            f"Entity: {self.entity_code}, "
            f"Type: {self.test_type}, "
            f"Function: {self.function_num}, "
            f"Scenario: {self.scenario}, "
            f"Test: {self.test_case}, "
            f"Instance: {self.instance}"
        )


class SpecQLUUID:
    """UUID-like object that preserves the custom encoded string representation"""

    def __init__(self, s: str):
        self._str = s

    def __str__(self) -> str:
        return self._str

    def __repr__(self) -> str:
        return f"SpecQLUUID('{self._str}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, UUID):
            return self._str == str(other)
        if isinstance(other, SpecQLUUID):
            return self._str == other._str
        return False

    def __hash__(self) -> int:
        return hash(self._str)


class SpecQLUUIDGenerator:
    """
    Generate encoded UUIDs for SpecQL test data

    Pattern: EEEEETTF-FFFF-0SSS-TTTT-00000000IIII

    Example:
        gen = SpecQLUUIDGenerator.for_entity("Contact", entity_code="012321")
        uuid = gen.generate(scenario=1000, instance=1)
        # Result: "01232121-0000-0001-0001-000000000001"
    """

    # Test type codes
    TEST_TYPES = {"general_seed": "21", "mutation_test": "22", "query_test": "23", "staging": "00"}

    def __init__(
        self,
        entity_name: str,
        entity_code: str,  # From metadata: base_uuid_prefix
        test_type: str = "general_seed",
        function_num: int | None = None,
    ):
        self.entity_name = entity_name
        self.entity_code = entity_code.zfill(6)  # Ensure 6 digits
        self.test_type_code = self.TEST_TYPES[test_type]
        self.function_num = function_num

    @classmethod
    def from_metadata(
        cls, entity_config: dict, test_type: str = "general_seed"
    ) -> "SpecQLUUIDGenerator":
        """Create from test metadata entity config"""
        return cls(
            entity_name=entity_config["entity_name"],
            entity_code=entity_config["base_uuid_prefix"],
            test_type=test_type,
        )

    def generate(self, scenario: int = 0, instance: int = 1, test_case: int = 0) -> SpecQLUUID:
        """
        Generate encoded UUID

        Args:
            scenario: Scenario code (0=default, 1000=dedup, 2000=alt, etc.)
            instance: Instance number (sequential: 1, 2, 3...)
            test_case: Test case number (for multiple tests per scenario)

        Returns:
            UUID with encoded components

        Example:
            >>> gen = SpecQLUUIDGenerator("Contact", "012321")
            >>> str(gen.generate(scenario=1000, instance=5))
            '01232121-0000-0001-0005-000000000005'
        """
        # Part 1: EEEEETT (8 hex chars) - entity code + test type
        part1 = f"{self.entity_code}{self.test_type_code}"

        # Part 2: FFFF (4 hex chars) - function number as decimal digits
        if self.function_num:
            func_str = str(self.function_num).zfill(4)[-4:]
        else:
            func_str = "0000"
        part2 = func_str

        # Part 3: 4SSS (4 hex chars) - Version 4 + scenario high 3 digits
        scenario_str = str(scenario).zfill(4)
        part3 = f"4{scenario_str[0:3]}"

        # Part 4: 8STT (4 hex chars) - Variant 8 + scenario low digit + test case (2 digits)
        part4 = f"8{scenario_str[3]}{str(test_case).zfill(2)}"

        # Part 5: 00000000IIII (12 hex chars) - Instance as 12 digits
        part5 = str(instance).zfill(12)

        uuid_str = f"{part1}-{part2}-{part3}-{part4}-{part5}"
        return SpecQLUUID(uuid_str)

    def generate_batch(
        self, count: int, scenario: int = 0, start_instance: int = 1
    ) -> list[SpecQLUUID]:
        """Generate batch of UUIDs with sequential instances"""
        return [self.generate(scenario=scenario, instance=start_instance + i) for i in range(count)]

    @staticmethod
    def decode(uuid: UUID) -> UUIDComponents:
        """
        Decode UUID into components

        Example:
            >>> components = SpecQLUUIDGenerator.decode(
            ...     UUID("01232122-3201-0001-0005-000000000001")
            ... )
            >>> components.entity_code
            '012321'
            >>> components.scenario
            1000
        """
        s = str(uuid).replace("-", "")

        return UUIDComponents(
            entity_code=s[0:6],
            test_type=s[6:8],
            function_num=s[8:12],
            scenario=int(s[13:16] + s[17]),
            test_case=int(s[18:20]),
            instance=int(s[24:36]),
        )
