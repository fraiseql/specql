package com.example.demo.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;

/**
 * Address embeddable for location information.
 */
@Embeddable
public class Address {

    @Column(name = "street_address", length = 255)
    @Size(max = 255, message = "Street address must be less than 255 characters")
    private String streetAddress;

    @Column(length = 100)
    @Size(max = 100, message = "City must be less than 100 characters")
    private String city;

    @Column(length = 20)
    @Size(max = 20, message = "State/Province must be less than 20 characters")
    private String state;

    @Column(name = "postal_code", length = 10)
    @Size(max = 10, message = "Postal code must be less than 10 characters")
    private String postalCode;

    @Column(length = 100)
    @Size(max = 100, message = "Country must be less than 100 characters")
    private String country;

    // Constructors
    public Address() {}

    public Address(String streetAddress, String city, String state, String postalCode, String country) {
        this.streetAddress = streetAddress;
        this.city = city;
        this.state = state;
        this.postalCode = postalCode;
        this.country = country;
    }

    // Getters and Setters
    public String getStreetAddress() { return streetAddress; }
    public void setStreetAddress(String streetAddress) { this.streetAddress = streetAddress; }

    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public String getPostalCode() { return postalCode; }
    public void setPostalCode(String postalCode) { this.postalCode = postalCode; }

    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    // Helper methods
    public String getFullAddress() {
        StringBuilder sb = new StringBuilder();
        if (streetAddress != null) sb.append(streetAddress);
        if (city != null) {
            if (sb.length() > 0) sb.append(", ");
            sb.append(city);
        }
        if (state != null) {
            if (sb.length() > 0) sb.append(", ");
            sb.append(state);
        }
        if (postalCode != null) {
            if (sb.length() > 0) sb.append(" ");
            sb.append(postalCode);
        }
        if (country != null) {
            if (sb.length() > 0) sb.append(", ");
            sb.append(country);
        }
        return sb.toString();
    }
}