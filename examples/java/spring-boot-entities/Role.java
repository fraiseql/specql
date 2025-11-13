package com.example.demo.model;

/**
 * User role enumeration.
 */
public enum Role {
    ADMIN("System Administrator", "Full system access"),
    MANAGER("Manager", "Manage teams and projects"),
    USER("User", "Standard user access"),
    GUEST("Guest", "Limited read-only access");

    private final String displayName;
    private final String description;

    Role(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }

    public boolean isAdminRole() {
        return this == ADMIN;
    }

    public boolean hasManagementAccess() {
        return this == ADMIN || this == MANAGER;
    }
}