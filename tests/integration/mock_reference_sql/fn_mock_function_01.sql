
        CREATE OR REPLACE FUNCTION crm.create_contact(p_email TEXT, p_name TEXT)
        RETURNS UUID AS $$
        DECLARE v_id UUID;
        BEGIN
            INSERT INTO tb_contact (email, name) VALUES (p_email, p_name) RETURNING id INTO v_id;
            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
