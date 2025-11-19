"""
Unit tests for Java action parser - Spring Boot framework

Your responsibility: Ensure these tests cover all Spring Boot patterns
"""

import pytest

from src.reverse_engineering.java_action_parser import JavaActionParser


class TestSpringBootParser:
    """Test Spring Boot-specific action parsing"""

    @pytest.fixture
    def parser(self):
        return JavaActionParser()

    def test_post_mapping(self, parser):
        """Test extracting CREATE action from @PostMapping"""
        java_code = """
package com.example.api;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/contacts")
public class ContactController {

    @PostMapping
    public ContactResponse createContact(@RequestBody ContactRequest request) {
        return new ContactResponse();
    }
}
"""
        # EXPECTED TO FAIL: Parser not implemented yet
        actions = parser.extract_actions_from_code(java_code)

        assert len(actions) == 1
        assert actions[0]["name"] == "createContact"
        assert actions[0]["type"] == "create"
        assert actions[0]["http_method"] == "POST"
        assert actions[0]["path"] == "/contacts"
        assert actions[0]["has_request_body"] is True

    def test_get_mapping_with_path_variable(self, parser):
        """Test extracting READ action with path variable"""
        java_code = """
@RestController
@RequestMapping("/contacts")
public class ContactController {

    @GetMapping("/{id}")
    public Contact getContact(@PathVariable Long id) {
        return contactService.findById(id);
    }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert len(actions) == 1
        assert actions[0]["type"] == "read"
        assert actions[0]["http_method"] == "GET"
        assert actions[0]["path"] == "/contacts/{id}"
        assert "id" in actions[0]["parameters"]

    def test_put_mapping(self, parser):
        """Test extracting UPDATE action from @PutMapping"""
        java_code = """
@RestController
public class ContactController {

    @PutMapping("/contacts/{id}")
    public Contact updateContact(@PathVariable Long id, @RequestBody ContactRequest request) {
        return contactService.update(id, request);
    }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "update"
        assert actions[0]["http_method"] == "PUT"

    def test_delete_mapping(self, parser):
        """Test extracting DELETE action"""
        java_code = """
@RestController
public class ContactController {

    @DeleteMapping("/contacts/{id}")
    public void deleteContact(@PathVariable Long id) {
        contactService.delete(id);
    }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "delete"
        assert actions[0]["http_method"] == "DELETE"

    def test_request_mapping_with_method(self, parser):
        """Test older @RequestMapping with method parameter"""
        java_code = """
@RestController
public class ContactController {

    @RequestMapping(value = "/contacts", method = RequestMethod.POST)
    public Contact createContact(@RequestBody ContactRequest request) {
        return contactService.create(request);
    }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "create"
        assert actions[0]["http_method"] == "POST"

    def test_multiple_methods_in_controller(self, parser):
        """Test extracting multiple actions from single controller"""
        java_code = """
@RestController
@RequestMapping("/contacts")
public class ContactController {

    @PostMapping
    public Contact create(@RequestBody ContactRequest req) { }

    @GetMapping
    public List<Contact> list() { }

    @GetMapping("/{id}")
    public Contact get(@PathVariable Long id) { }

    @PutMapping("/{id}")
    public Contact update(@PathVariable Long id, @RequestBody ContactRequest req) { }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) { }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert len(actions) == 5
        assert actions[0]["type"] == "create"
        assert actions[1]["type"] == "read"  # list
        assert actions[2]["type"] == "read"  # get
        assert actions[3]["type"] == "update"
        assert actions[4]["type"] == "delete"

    def test_request_param_detection(self, parser):
        """Test detecting @RequestParam query parameters"""
        java_code = """
@RestController
public class ContactController {

    @GetMapping("/contacts/search")
    public List<Contact> search(@RequestParam String email) {
        return contactService.findByEmail(email);
    }
}
"""
        actions = parser.extract_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "read"
        assert "email" in actions[0]["query_params"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
