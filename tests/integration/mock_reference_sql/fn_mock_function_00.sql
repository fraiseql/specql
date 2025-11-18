
        CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
        RETURNS NUMERIC AS $$
        DECLARE v_total NUMERIC := 0;
        BEGIN
            SELECT SUM(amount) INTO v_total FROM tb_order_line WHERE order_id = p_order_id;
            RETURN v_total;
        END;
        $$ LANGUAGE plpgsql;
        