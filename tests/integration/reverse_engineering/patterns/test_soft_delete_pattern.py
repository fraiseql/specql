"""
Universal Soft Delete Pattern Detection Tests
"""

import pytest

from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestSoftDeletePatternRust:
    """Test soft delete detection in Rust"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_rust_option_deleted_at(self, detector):
        """Test Rust with Option<DateTime> deleted_at"""
        rust_code = """
use chrono::{DateTime, Utc};

pub struct Contact {
    pub email: String,
    pub deleted_at: Option<DateTime<Utc>>,
}

impl Contact {
    pub fn delete(id: i32) -> Result<()> {
        diesel::update(contacts::table.find(id))
            .set(contacts::deleted_at.eq(Some(Utc::now())))
            .execute(conn)?;
        Ok(())
    }

    pub fn list_active() -> Result<Vec<Contact>> {
        contacts::table
            .filter(contacts::deleted_at.is_null())
            .load(conn)
    }

    pub fn restore(id: i32) -> Result<()> {
        diesel::update(contacts::table.find(id))
            .set(contacts::deleted_at.eq(None::<DateTime<Utc>>))
            .execute(conn)?;
        Ok(())
    }
}
        """

        # EXPECTED TO FAIL: Pattern detector not implemented
        patterns = detector.detect(rust_code, language="rust")

        assert any(p.name == "soft_delete" for p in patterns)
        sd = next(p for p in patterns if p.name == "soft_delete")

        assert sd.confidence >= 0.94
        assert "deleted_at" in " ".join(sd.evidence).lower()
        assert sd.suggested_stdlib == "crud/soft_delete"


class TestSoftDeletePatternPython:
    """Test soft delete detection in Python"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_python_datetime_deleted_at(self, detector):
        """Test Python with datetime deleted_at"""
        python_code = """
from datetime import datetime
from typing import Optional

class Contact:
    deleted_at: Optional[datetime] = None

    def delete(self):
        self.deleted_at = datetime.now()
        # NOT db.session.delete(self)

    def restore(self):
        self.deleted_at = None

    @classmethod
    def list_active(cls):
        return cls.query.filter(cls.deleted_at.is_(None)).all()

    @classmethod
    def list_deleted(cls):
        return cls.query.filter(cls.deleted_at.isnot(None)).all()
        """

        patterns = detector.detect(python_code, language="python")

        # EXPECTED TO FAIL
        assert any(p.name == "soft_delete" for p in patterns)
        assert patterns[0].confidence >= 0.94


class TestSoftDeletePatternSQL:
    """Test soft delete detection in SQL"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_sql_deleted_at_column(self, detector):
        """Test SQL table with deleted_at"""
        sql_code = """
CREATE TABLE tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE FUNCTION delete_contact(p_id INT) AS $$
BEGIN
    UPDATE tb_contact
    SET deleted_at = NOW()
    WHERE pk_contact = p_id;
    -- NOTE: Not using DELETE FROM
END;
$$ LANGUAGE plpgsql;

CREATE VIEW vw_active_contacts AS
SELECT * FROM tb_contact
WHERE deleted_at IS NULL;

CREATE FUNCTION restore_contact(p_id INT) AS $$
BEGIN
    UPDATE tb_contact
    SET deleted_at = NULL
    WHERE pk_contact = p_id;
END;
$$ LANGUAGE plpgsql;
        """

        patterns = detector.detect(sql_code, language="sql")

        # EXPECTED TO FAIL
        assert any(p.name == "soft_delete" for p in patterns)
        sd = next(p for p in patterns if p.name == "soft_delete")
        assert sd.confidence >= 0.94


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
