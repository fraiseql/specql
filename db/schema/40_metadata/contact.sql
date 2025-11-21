-- FraiseQL Mutation Annotations (Team D)
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   input=QualifyLeadInput
   success_type=QualifyLeadSuccess
   error_type=QualifyLeadError
   primary_entity=Contact
   metadata_mapping={}';

COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact
   input=CreateContactInput
   success_type=CreateContactSuccess
   error_type=CreateContactError
   primary_entity=Contact
   metadata_mapping={}';
