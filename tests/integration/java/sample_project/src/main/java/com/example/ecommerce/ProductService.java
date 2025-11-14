package com.example.ecommerce;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class ProductService {

    @Autowired
    private ProductRepository productRepository;

    public List<Product> findAllActive() {
        return productRepository.findByActiveTrue();
    }

    public Optional<Product> findById(Long id) {
        return productRepository.findById(id);
    }

    public Product save(Product product) {
        return productRepository.save(product);
    }

    public void deleteById(Long id) {
        productRepository.deleteById(id);
    }

    public List<Product> findByCategory(Category category) {
        return productRepository.findByCategoryAndActiveTrue(category);
    }

    public List<Product> findByPriceRange(Integer minPrice, Integer maxPrice) {
        return productRepository.findByPriceRange(minPrice, maxPrice);
    }

    public Optional<Product> findByName(String name) {
        return productRepository.findByName(name);
    }
}