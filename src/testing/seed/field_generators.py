"""Field value generators for SpecQL test data"""

import random
from typing import Any

from faker import Faker


class FieldValueGenerator:
    """Generate field values based on type and metadata"""

    def __init__(self, seed: int | None = None):
        """
        Args:
            seed: Random seed for deterministic generation
        """
        self.faker = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate(self, field_mapping: dict[str, Any], context: dict[str, Any] = None) -> Any:
        """
        Generate value for field based on mapping

        Args:
            field_mapping: From test_metadata.tb_field_generator_mapping
            context: Previously generated field values (for dependencies)

        Returns:
            Generated value (type depends on field)
        """
        if context is None:
            context = {}

        generator_type = field_mapping["generator_type"]

        if generator_type == "random":
            return self._generate_random(field_mapping)
        elif generator_type == "fixed":
            return field_mapping["generator_params"]["fixed_value"]
        elif generator_type == "sequence":
            return self._generate_sequence(field_mapping, context)
        else:
            raise ValueError(f"Unsupported generator type: {generator_type}")

    def _generate_random(self, mapping: dict[str, Any]) -> Any:
        """Generate random value based on field type"""
        field_type = mapping["field_type"]

        # Use example values if provided
        if mapping.get("example_values"):
            return random.choice(mapping["example_values"])

        # Rich scalar types
        if field_type == "email":
            return self.faker.email()

        elif field_type == "phoneNumber":
            return self.faker.phone_number()

        elif field_type == "url":
            return self.faker.url()

        elif field_type == "money":
            return round(random.uniform(10, 10000), 2)

        elif field_type == "percentage":
            return round(random.uniform(0, 100), 2)

        elif field_type == "ipAddress":
            return self.faker.ipv4()

        elif field_type == "macAddress":
            return self.faker.mac_address()

        # Basic types
        elif field_type == "text":
            return self.faker.sentence(nb_words=3).rstrip(".")

        elif field_type == "integer":
            dist = mapping.get("seed_distribution", {})
            min_val = dist.get("min", 1)
            max_val = dist.get("max", 1000)
            return random.randint(min_val, max_val)

        elif field_type == "boolean":
            return random.choice([True, False])

        elif field_type.startswith("enum("):
            # Parse: "enum(lead, qualified, customer)" → ["lead", "qualified", "customer"]
            if mapping.get("enum_values"):
                values = mapping["enum_values"]
            else:
                values = field_type[5:-1].split(",")
                values = [v.strip() for v in values]
            return random.choice(values)

        elif field_type == "date":
            return self.faker.date_between(start_date="-1y", end_date="today")

        elif field_type == "timestamptz":
            return self.faker.date_time_between(start_date="-1y", end_date="now")

        else:
            # Fallback
            return None

    def _generate_sequence(self, mapping: dict, context: dict) -> Any:
        """Generate sequential value"""
        params = mapping.get("generator_params", {})
        start = params.get("start", 1)
        step = params.get("step", 1)
        instance_num = context.get("instance_num", 1)

        return start + (instance_num - 1) * step
