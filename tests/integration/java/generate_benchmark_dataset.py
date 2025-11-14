"""Generate 100-entity benchmark dataset for performance testing"""

from pathlib import Path


def generate_entity(index: int) -> str:
    """Generate a realistic JPA entity"""
    entity_name = f"Entity{index:03d}"

    return f"""package com.example.benchmark;

import javax.persistence.*;
import java.time.LocalDateTime;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;

@Entity
@Table(name = "tb_{entity_name.lower()}")
public class {entity_name} {{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column
    private String description;

    @Column(nullable = false)
    private Integer value{index};

    @Column
    private Boolean active = true;

    @Enumerated(EnumType.STRING)
    private Status{index} status;

    // Reference to another entity (circular dependencies)
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_related")
    private Entity{max(0, (index - 1) % 100):03d} related;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Column
    private LocalDateTime deletedAt;

    // Getters and setters omitted
}}
"""


def generate_enum(index: int) -> str:
    """Generate enum for entity"""
    return f"""package com.example.benchmark;

public enum Status{index} {{
    PENDING,
    ACTIVE,
    COMPLETED,
    ARCHIVED
}}
"""


def main():
    """Generate 100 entities + 100 enums"""
    output_dir = Path(
        "tests/integration/java/benchmark_dataset/src/main/java/com/example/benchmark"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating 100-entity benchmark dataset...")

    for i in range(100):
        # Generate entity
        entity_code = generate_entity(i)
        entity_file = output_dir / f"Entity{i:03d}.java"
        entity_file.write_text(entity_code)

        # Generate enum
        enum_code = generate_enum(i)
        enum_file = output_dir / f"Status{i}.java"
        enum_file.write_text(enum_code)

        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/100 entities...")

    print(f"✅ Generated 100 entities + 100 enums in {output_dir}")
    print(f"   Total files: 200")
    print(f"   Total lines: ~{100 * 30 + 100 * 7}")


if __name__ == "__main__":
    main()
