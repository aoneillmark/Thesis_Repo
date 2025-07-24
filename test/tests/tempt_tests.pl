% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("basic_hospitalization_covered_young_age", is_claim_covered(25, 50, sickness)).
% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("exclusion_military_service", is_claim_covered(30, 100, military_service)).
% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("exclusion_age_over_80", is_claim_covered(81, 200, accidental_injury)).
% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("exclusion_skydiver", is_claim_covered(40, 150, skydiving_injury)).
% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("wellness_visit_missed_late_claim", \+is_claim_covered(22, 300, sickness)).
% Args: ClaimantAge, HospitalizationDateRelative, ReasonForHospitalization
test("policy_cancellation_due_to_fraud", \+is_claim_covered(35, 180, sickness)).