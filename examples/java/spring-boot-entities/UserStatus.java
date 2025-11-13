package com.example.demo.model;

/**
 * User status enumeration.
 */
public enum UserStatus {
    ACTIVE("Active user account"),
    INACTIVE("Inactive user account"),
    SUSPENDED("Suspended user account"),
    PENDING("Pending activation");

    private final String description;

    UserStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    public boolean isActiveState() {
        return this == ACTIVE;
    }
}