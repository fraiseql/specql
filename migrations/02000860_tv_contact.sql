-- Table View: crm.tv_contact
-- Table view for Contact (read-optimized, denormalized)
CREATE TABLE crm.tv_contact (
    pk_contact INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_company INTEGER,
    company_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_contact_tenant ON crm.tv_contact(tenant_id);
CREATE INDEX idx_tv_contact_company_id ON crm.tv_contact(company_id);
CREATE INDEX idx_tv_contact_data ON crm.tv_contact USING GIN(data);

-- Refresh function for tv_contact
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION crm.refresh_tv_contact(
    p_pk_contact INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM crm.tv_contact
    WHERE p_pk_contact IS NULL OR pk_contact = p_pk_contact;

    -- Insert refreshed data
    INSERT INTO crm.tv_contact (
        pk_contact, id, tenant_id, fk_company, company_id, data
    )
    SELECT
        base.pk_contact,
        base.id,
        base.tenant_id,
        base.fk_company,
        tv_company.id AS company_id,
        jsonb_build_object('company', tv_company.data, 'email', base.email, 'first_name', base.first_name, 'last_name', base.last_name, 'status', base.status, 'phone', base.phone, 'notes', base.notes) AS data
    FROM crm.tb_contact base
    LEFT JOIN public.tv_company tv_company ON tv_company.pk_company = base.fk_company
    WHERE base.deleted_at IS NULL
      AND (p_pk_contact IS NULL OR base.pk_contact = p_pk_contact);
END;
$$ LANGUAGE plpgsql;