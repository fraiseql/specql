"""Unit tests for CursorOperationsParser"""

from reverse_engineering.cursor_operations_parser import CursorOperationsParser


class TestCursorOperationsParser:
    """Test cursor operations parsing in isolation"""

    def setup_method(self):
        self.parser = CursorOperationsParser()

    def test_parse_cursor_declaration_in_declare_block(self):
        """Test parsing cursor declaration inside DECLARE block"""
        sql = """
        DECLARE
            contact_cursor CURSOR FOR SELECT * FROM contacts WHERE status = 'pending';
            contact_record record;
        BEGIN
            OPEN contact_cursor;
        """

        steps = self.parser.parse(sql)

        # Should find cursor_declare step
        cursor_declares = [s for s in steps if s.type == "cursor_declare"]
        assert len(cursor_declares) == 1
        assert cursor_declares[0].variable_name == "contact_cursor"
        assert "SELECT * FROM contacts" in cursor_declares[0].sql

    def test_parse_multiple_cursor_declarations(self):
        """Test parsing multiple cursor declarations"""
        sql = """
        DECLARE
            cursor1 CURSOR FOR SELECT * FROM table1;
            cursor2 CURSOR FOR SELECT id, name FROM table2 WHERE active = true;
        BEGIN
            -- operations
        """

        steps = self.parser.parse(sql)

        cursor_declares = [s for s in steps if s.type == "cursor_declare"]
        assert len(cursor_declares) == 2
        assert cursor_declares[0].variable_name == "cursor1"
        assert cursor_declares[1].variable_name == "cursor2"

    def test_parse_cursor_operations_in_loop(self):
        """Test parsing cursor operations inside LOOP"""
        # Note: CursorOperationsParser expects the content between BEGIN and END
        # (without the BEGIN/END keywords)
        sql = """
            OPEN contact_cursor;
            LOOP
                FETCH contact_cursor INTO contact_record;
                EXIT WHEN NOT FOUND;
            END LOOP;
            CLOSE contact_cursor;
        """

        steps = self.parser.parse(sql)

        # Should find open, fetch, close
        assert any(s.type == "cursor_open" for s in steps)
        assert any(s.type == "cursor_fetch" for s in steps)
        assert any(s.type == "cursor_close" for s in steps)

    def test_parse_fetch_with_into_clause(self):
        """Test parsing FETCH with INTO clause"""
        sql = "FETCH contact_cursor INTO contact_record;"

        steps = self.parser.parse(sql)

        fetch_steps = [s for s in steps if s.type == "cursor_fetch"]
        assert len(fetch_steps) == 1
        assert fetch_steps[0].variable_name == "contact_cursor"
        assert fetch_steps[0].store_result == "contact_record"
