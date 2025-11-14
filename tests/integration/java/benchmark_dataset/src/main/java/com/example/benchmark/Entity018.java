package com.example.benchmark;

import javax.persistence.*;
import java.time.LocalDateTime;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;

@Entity
@Table(name = "tb_entity018")
public class Entity018 {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column
    private String description;

    @Column(nullable = false)
    private Integer value18;

    @Column
    private Boolean active = true;

    @Enumerated(EnumType.STRING)
    private Status18 status;

    // Reference to another entity (circular dependencies)
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_related")
    private Entity017 related;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Column
    private LocalDateTime deletedAt;

    // Getters and setters omitted
}
