
        CREATE OR REPLACE FUNCTION crm.get_contact(p_id UUID)
        RETURNS tb_contact AS $$
        BEGIN
            RETURN (SELECT * FROM tb_contact WHERE id = p_id);
        END;
        $$ LANGUAGE plpgsql;
        