
        CREATE OR REPLACE FUNCTION crm.delete_contact(p_id UUID)
        RETURNS VOID AS $$
        BEGIN
            DELETE FROM tb_contact WHERE id = p_id;
        END;
        $$ LANGUAGE plpgsql;
