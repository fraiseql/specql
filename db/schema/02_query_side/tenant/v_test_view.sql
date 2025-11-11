-- @fraiseql:view
-- @fraiseql:description Hierarchical count of Allocation by Location
CREATE OR REPLACE VIEW tenant.test_view AS
SELECT
    pk_location AS pk_location,


    COUNT(CASE WHEN child.location_id = parent.pk_location THEN 1 END) AS direct_direct,




FROM tb_location parent
LEFT JOIN tb_allocation child
    ON child.location_id = parent.pk_location
WHERE parent.deleted_at IS NULL
  AND (child.deleted_at IS NULL OR child.pk_allocation IS NULL)

  AND parent.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid

GROUP BY parent.pk_location;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_view_location
    ON tenant.test_view(pk_location);

