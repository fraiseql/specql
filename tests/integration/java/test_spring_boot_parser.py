"""
Integration tests for Spring Boot pattern recognition
"""

import pytest
from src.reverse_engineering.java.spring_parser import SpringParser, SpringParseConfig


class TestSpringBootIntegration:
    """Integration tests for Spring Boot parsing"""

    def setup_method(self):
        self.parser = SpringParser()

    def test_parse_spring_boot_controller(self):
        """Test parsing a complete Spring Boot controller"""
        java_code = """
package com.example.demo;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }

    @GetMapping("/{id}")
    public User getUserById(@PathVariable Long id) {
        return userService.getUserById(id);
    }

    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.createUser(user);
    }

    @PutMapping("/{id}")
    public User updateUser(@PathVariable Long id, @RequestBody User user) {
        return userService.updateUser(id, user);
    }

    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
    }
}
"""

        # Write to temporary file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_file = f.name

        try:
            result = self.parser.parse_file(temp_file)

            assert len(result.errors) == 0
            assert len(result.components) == 1

            component = result.components[0]
            assert component.class_name == "UserController"
            assert component.component_type == "rest_controller"
            assert component.base_path == "/api/users"
            assert len(component.methods) == 5

            # Check actions
            assert len(result.actions) == 5

            # Check specific actions
            action_names = [action.name for action in result.actions]
            assert "get_api_users" in action_names
            assert "get_api_users_{id}" in action_names
            assert "post_api_users" in action_names
            assert "put_api_users_{id}" in action_names
            assert "delete_api_users_{id}" in action_names

        finally:
            os.unlink(temp_file)

    def test_parse_spring_boot_service(self):
        """Test parsing a Spring Boot service"""
        java_code = """
package com.example.demo;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    @Transactional(readOnly = true)
    public User getUserById(Long id) {
        return userRepository.findById(id).orElse(null);
    }

    @Transactional
    public User createUser(User user) {
        return userRepository.save(user);
    }

    @Transactional
    public User updateUser(Long id, User user) {
        user.setId(id);
        return userRepository.save(user);
    }

    @Transactional
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }
}
"""

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_file = f.name

        try:
            result = self.parser.parse_file(temp_file)

            assert len(result.errors) == 0
            assert len(result.components) == 1

            component = result.components[0]
            assert component.class_name == "UserService"
            assert component.component_type == "service"
            assert len(component.methods) == 5

            # Check actions
            assert len(result.actions) == 5

        finally:
            os.unlink(temp_file)

    def test_parse_spring_boot_repository(self):
        """Test parsing a Spring Data repository"""
        java_code = """
package com.example.demo;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    List<User> findByEmail(String email);

    List<User> findByStatus(String status);

    Optional<User> findByUsername(String username);

    boolean existsByEmail(String email);

    long countByStatus(String status);

    @Query("SELECT u FROM User u WHERE u.createdDate > :date")
    List<User> findUsersCreatedAfter(@Param("date") LocalDateTime date);

    void deleteByEmail(String email);
}
"""

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_file = f.name

        try:
            result = self.parser.parse_file(temp_file)

            assert len(result.errors) == 0
            assert len(result.components) == 1

            component = result.components[0]
            assert component.class_name == "UserRepository"
            assert component.component_type == "repository"
            assert (
                len(component.methods) == 7
            )  # All repository methods should be detected

            # Check actions
            assert len(result.actions) == 7

        finally:
            os.unlink(temp_file)

    def test_parse_spring_boot_configuration(self):
        """Test parsing a Spring Boot configuration class"""
        java_code = """
package com.example.demo;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public UserDetailsService userDetailsService() {
        return new CustomUserDetailsService();
    }
}
"""

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_file = f.name

        try:
            result = self.parser.parse_file(temp_file)

            assert len(result.errors) == 0
            assert len(result.components) == 1

            component = result.components[0]
            assert component.class_name == "SecurityConfig"
            assert component.component_type == "configuration"
            assert len(component.methods) == 2

            # Check actions
            assert len(result.actions) == 2

        finally:
            os.unlink(temp_file)

    def test_parse_directory_with_multiple_components(self):
        """Test parsing a directory with multiple Spring components"""
        import tempfile
        import os

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Create controller
            controller_code = """
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping
    public List<Product> getProducts() { return null; }
}
"""
            with open(os.path.join(temp_dir, "ProductController.java"), "w") as f:
                f.write(controller_code)

            # Create service
            service_code = """
@Service
public class ProductService {
    public List<Product> getProducts() { return null; }
}
"""
            with open(os.path.join(temp_dir, "ProductService.java"), "w") as f:
                f.write(service_code)

            # Create repository
            repo_code = """
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByCategory(String category);
}
"""
            with open(os.path.join(temp_dir, "ProductRepository.java"), "w") as f:
                f.write(repo_code)

            results = self.parser.parse_directory(temp_dir)

            assert len(results) == 3

            # Check that all components were found
            component_types = [
                result.components[0].component_type
                for result in results
                if result.components
            ]
            assert "rest_controller" in component_types
            assert "service" in component_types
            assert "repository" in component_types

        finally:
            import shutil

            shutil.rmtree(temp_dir)
