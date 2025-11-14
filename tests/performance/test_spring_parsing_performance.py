"""
Performance benchmarks for Spring Boot parsing
"""

import pytest
import time
import tempfile
import os
from src.reverse_engineering.java.spring_parser import SpringParser


class TestSpringParsingPerformance:
    """Performance tests for Spring Boot parsing"""

    def setup_method(self):
        self.parser = SpringParser()

    def test_parse_small_spring_project(self):
        """Benchmark parsing a small Spring Boot project (3-5 files)"""
        java_files = self._create_small_spring_project()

        start_time = time.time()
        results = []

        for file_path, _ in java_files:
            result = self.parser.parse_file(file_path)
            results.append(result)

        end_time = time.time()
        parse_time = end_time - start_time

        # Validate results
        total_components = sum(len(result.components) for result in results)
        total_actions = sum(len(result.actions) for result in results)

        assert total_components == 3  # Controller, Service, Repository
        assert total_actions >= 5  # At least 5 methods

        # Performance assertion: should parse in under 1 second
        assert parse_time < 1.0, f"Parsing took {parse_time:.2f}s, expected < 1.0s"

        print(
            f"Small project parsing: {parse_time:.3f}s for {total_components} components, {total_actions} actions"
        )

    def test_parse_medium_spring_project(self):
        """Benchmark parsing a medium Spring Boot project (10-15 files)"""
        java_files = self._create_medium_spring_project()

        start_time = time.time()
        results = []

        for file_path, _ in java_files:
            result = self.parser.parse_file(file_path)
            results.append(result)

        end_time = time.time()
        parse_time = end_time - start_time

        # Validate results
        total_components = sum(len(result.components) for result in results)
        total_actions = sum(len(result.actions) for result in results)

        assert total_components >= 8  # Multiple controllers, services, repositories
        assert total_actions >= 20  # Many methods

        # Performance assertion: should parse in under 3 seconds
        assert parse_time < 3.0, f"Parsing took {parse_time:.2f}s, expected < 3.0s"

        print(
            f"Medium project parsing: {parse_time:.3f}s for {total_components} components, {total_actions} actions"
        )

    def _create_small_spring_project(self):
        """Create a small Spring Boot project for testing"""
        temp_dir = tempfile.mkdtemp()
        files = []

        # UserController
        controller_code = """
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping public List<User> getUsers() { return null; }
    @PostMapping public User createUser(@RequestBody User user) { return null; }
    @GetMapping("/{id}") public User getUser(@PathVariable Long id) { return null; }
}
"""
        controller_path = os.path.join(temp_dir, "UserController.java")
        with open(controller_path, "w") as f:
            f.write(controller_code)
        files.append((controller_path, controller_code))

        # UserService
        service_code = """
@Service
public class UserService {
    @Transactional public User createUser(User user) { return null; }
    @Transactional(readOnly = true) public User getUser(Long id) { return null; }
}
"""
        service_path = os.path.join(temp_dir, "UserService.java")
        with open(service_path, "w") as f:
            f.write(service_code)
        files.append((service_path, service_code))

        # UserRepository
        repo_code = """
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByEmail(String email);
    User save(User user);
}
"""
        repo_path = os.path.join(temp_dir, "UserRepository.java")
        with open(repo_path, "w") as f:
            f.write(repo_code)
        files.append((repo_path, repo_code))

        return files

    def _create_medium_spring_project(self):
        """Create a medium Spring Boot project for testing"""
        temp_dir = tempfile.mkdtemp()
        files = []

        # Add the small project files
        small_files = self._create_small_spring_project()
        for file_path, content in small_files:
            # Copy to new location
            new_path = os.path.join(temp_dir, os.path.basename(file_path))
            with open(new_path, "w") as f:
                f.write(content)
            files.append((new_path, content))

        # Add more components
        components = [
            (
                "ProductController",
                """
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping public List<Product> getProducts() { return null; }
    @PostMapping public Product createProduct(@RequestBody Product product) { return null; }
    @GetMapping("/{id}") public Product getProduct(@PathVariable Long id) { return null; }
    @PutMapping("/{id}") public Product updateProduct(@PathVariable Long id, @RequestBody Product product) { return null; }
}
""",
            ),
            (
                "ProductService",
                """
@Service
public class ProductService {
    @Transactional public Product createProduct(Product product) { return null; }
    @Transactional(readOnly = true) public Product getProduct(Long id) { return null; }
    @Transactional public Product updateProduct(Long id, Product product) { return null; }
}
""",
            ),
            (
                "ProductRepository",
                """
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByCategory(String category);
    List<Product> findByPriceGreaterThan(BigDecimal price);
    Product save(Product product);
    void deleteById(Long id);
}
""",
            ),
            (
                "OrderController",
                """
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    @GetMapping public List<Order> getOrders() { return null; }
    @PostMapping public Order createOrder(@RequestBody Order order) { return null; }
}
""",
            ),
            (
                "OrderService",
                """
@Service
public class OrderService {
    @Transactional public Order createOrder(Order order) { return null; }
    @Transactional(readOnly = true) public List<Order> getOrders() { return null; }
}
""",
            ),
        ]

        for class_name, code in components:
            file_path = os.path.join(temp_dir, f"{class_name}.java")
            with open(file_path, "w") as f:
                f.write(code)
            files.append((file_path, code))

        return files
