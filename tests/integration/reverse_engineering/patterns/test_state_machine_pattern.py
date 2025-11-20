"""
Universal State Machine Pattern Detection Tests

Tests detection across all languages: Rust, Python, Java, SQL
"""

import pytest

from reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestStateMachinePatternRust:
    """Test state machine detection in Rust"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_rust_basic_state_machine(self, detector):
        """Test basic Rust state machine with enum"""
        rust_code = """
pub enum OrderStatus {
    Pending,
    Shipped,
    Delivered,
}

pub struct Order {
    pub status: OrderStatus,
}

impl Order {
    pub fn ship(&mut self) -> Result<()> {
        if self.status != OrderStatus::Pending {
            return Err(Error::InvalidStatus);
        }
        self.status = OrderStatus::Shipped;
        Ok(())
    }

    pub fn deliver(&mut self) -> Result<()> {
        if self.status != OrderStatus::Shipped {
            return Err(Error::InvalidStatus);
        }
        self.status = OrderStatus::Delivered;
        Ok(())
    }
}
        """

        # EXPECTED TO FAIL: Pattern detector not implemented
        patterns = detector.detect(rust_code, language="rust")

        assert any(p.name == "state_machine" for p in patterns)
        state_machine = next(p for p in patterns if p.name == "state_machine")

        assert state_machine.confidence >= 0.85
        assert (
            "status" in state_machine.evidence
            or "state" in " ".join(state_machine.evidence).lower()
        )
        assert state_machine.suggested_stdlib == "state_machine/transition"

    def test_rust_string_based_status(self, detector):
        """Test Rust state machine with String status"""
        rust_code = """
pub struct Contact {
    pub status: String,  // "lead", "qualified", "customer"
}

impl Contact {
    pub fn qualify(&mut self) -> Result<()> {
        if self.status != "lead" {
            return Err(Error::MustBeLead);
        }
        self.status = "qualified".to_string();
        Ok(())
    }

    pub fn convert_to_customer(&mut self) -> Result<()> {
        if self.status != "qualified" {
            return Err(Error::MustBeQualified);
        }
        self.status = "customer".to_string();
        Ok(())
    }
}
        """

        patterns = detector.detect(rust_code, language="rust")

        # EXPECTED TO FAIL
        assert any(p.name == "state_machine" for p in patterns)
        assert patterns[0].confidence >= 0.80  # String-based slightly lower confidence


class TestStateMachinePatternPython:
    """Test state machine detection in Python"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_python_class_based_state_machine(self, detector):
        """Test Python class with status field and transitions"""
        python_code = """
class Order:
    def __init__(self):
        self.status = "pending"

    def ship(self):
        if self.status != "pending":
            raise ValueError("Order must be pending to ship")
        self.status = "shipped"

    def deliver(self):
        if self.status != "shipped":
            raise ValueError("Order must be shipped to deliver")
        self.status = "delivered"

    def cancel(self):
        if self.status not in ["pending", "shipped"]:
            raise ValueError("Cannot cancel delivered order")
        self.status = "cancelled"
        """

        patterns = detector.detect(python_code, language="python")

        # EXPECTED TO FAIL
        assert any(p.name == "state_machine" for p in patterns)
        sm = next(p for p in patterns if p.name == "state_machine")

        assert sm.confidence >= 0.85
        assert "3" in str(sm.evidence) or "transitions" in " ".join(sm.evidence).lower()

    def test_python_enum_status(self, detector):
        """Test Python with Enum status"""
        python_code = """
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class Order:
    def __init__(self):
        self.status = Status.PENDING

    def ship(self):
        if self.status != Status.PENDING:
            raise ValueError("Invalid status")
        self.status = Status.SHIPPED
        """

        patterns = detector.detect(python_code, language="python")

        # EXPECTED TO FAIL
        assert any(p.name == "state_machine" for p in patterns)
        assert patterns[0].confidence >= 0.90  # Enum-based = higher confidence


class TestStateMachinePatternSQL:
    """Test state machine detection in SQL"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_sql_plpgsql_state_machine(self, detector):
        """Test PL/pgSQL function with status transition"""
        sql_code = """
CREATE TABLE tb_order (
    pk_order INTEGER PRIMARY KEY,
    status TEXT NOT NULL
);

CREATE FUNCTION ship_order(p_order_id INT) AS $$
DECLARE
    v_status TEXT;
BEGIN
    SELECT status INTO v_status
    FROM tb_order
    WHERE pk_order = p_order_id;

    IF v_status != 'pending' THEN
        RAISE EXCEPTION 'Order must be pending to ship';
    END IF;

    UPDATE tb_order
    SET status = 'shipped'
    WHERE pk_order = p_order_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION deliver_order(p_order_id INT) AS $$
BEGIN
    IF (SELECT status FROM tb_order WHERE pk_order = p_order_id) != 'shipped' THEN
        RAISE EXCEPTION 'Order must be shipped to deliver';
    END IF;

    UPDATE tb_order
    SET status = 'delivered'
    WHERE pk_order = p_order_id;
END;
$$ LANGUAGE plpgsql;
        """

        patterns = detector.detect(sql_code, language="sql")

        # EXPECTED TO FAIL
        assert any(p.name == "state_machine" for p in patterns)
        sm = next(p for p in patterns if p.name == "state_machine")

        assert sm.confidence >= 0.80
        assert "status" in " ".join(sm.evidence).lower()


class TestStateMachinePatternJava:
    """Test state machine detection in Java"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_java_jpa_entity_state_machine(self, detector):
        """Test Java entity with status transitions"""
        java_code = """
@Entity
public class Order {
    @Column(name = "status")
    private String status;

    public void ship() throws InvalidStatusException {
        if (!this.status.equals("pending")) {
            throw new InvalidStatusException("Must be pending");
        }
        this.status = "shipped";
    }

    public void deliver() throws InvalidStatusException {
        if (!this.status.equals("shipped")) {
            throw new InvalidStatusException("Must be shipped");
        }
        this.status = "delivered";
    }
}
        """

        patterns = detector.detect(java_code, language="java")

        # EXPECTED TO FAIL
        assert any(p.name == "state_machine" for p in patterns)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
