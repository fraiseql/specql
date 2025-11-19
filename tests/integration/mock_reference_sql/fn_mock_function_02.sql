
        CREATE OR REPLACE FUNCTION crm.update_contact_state(p_id UUID, p_state TEXT)
        RETURNS VOID AS $$
        BEGIN
            UPDATE tb_contact SET state = p_state WHERE id = p_id;
        END;
        $$ LANGUAGE plpgsql;
        