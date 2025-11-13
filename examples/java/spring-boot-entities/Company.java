package com.example.demo.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;
import java.util.Set;

/**
 * Company entity representing organizations.
 * Demonstrates embedded objects and complex relationships.
 */
@Entity
@Table(name = "companies")
public class Company {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    @NotBlank(message = "Company name is required")
    @Size(max = 100, message = "Company name must be less than 100 characters")
    private String name;

    @Column(length = 500)
    @Size(max = 500, message = "Description must be less than 500 characters")
    private String description;

    @Column(name = "website_url")
    private String websiteUrl;

    @Embedded
    private Address headquarters;

    @Column(name = "employee_count")
    @Min(value = 1, message = "Employee count must be at least 1")
    private Integer employeeCount;

    @Enumerated(EnumType.STRING)
    @Column(name = "company_size")
    private CompanySize size;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @OneToMany(mappedBy = "company", cascade = CascadeType.ALL)
    private Set<User> employees;

    // Constructors
    public Company() {}

    public Company(String name, String description) {
        this.name = name;
        this.description = description;
        this.createdAt = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getWebsiteUrl() { return websiteUrl; }
    public void setWebsiteUrl(String websiteUrl) { this.websiteUrl = websiteUrl; }

    public Address getHeadquarters() { return headquarters; }
    public void setHeadquarters(Address headquarters) { this.headquarters = headquarters; }

    public Integer getEmployeeCount() { return employeeCount; }
    public void setEmployeeCount(Integer employeeCount) { this.employeeCount = employeeCount; }

    public CompanySize getSize() { return size; }
    public void setSize(CompanySize size) { this.size = size; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public Set<User> getEmployees() { return employees; }
    public void setEmployees(Set<User> employees) { this.employees = employees; }

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}