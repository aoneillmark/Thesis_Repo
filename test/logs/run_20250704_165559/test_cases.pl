test("coverage for hospitalization due to sickness", "policy_in_effect(DateOfHospitalization) :- hospital_cash_benefit_policy_active_at(DateOfHospitalization).
test("policy cancellation due to fraud", "policy_not_canceled(Reason) :- reason_for_cancellation(fraud).
test("exclusion for skydiving injury", "benefit_excluded(injury_from_skydiving).
test("age exclusion for hospitalization", "benefit_excluded(hospitalization_at_age_80_or_greater).
test("wellness visit condition met", "wellness_visit_condition_met(DateOfWellnessVisit, EffectiveDate) :- DateOfWellnessVisit =< EffectiveDate + 6 months, DateOfWellnessVisit >= EffectiveDate + 7 months.").
test("policy in effect - valid conditions", policy_in_effect(signed_agreement, true, premium_paid, true, wellness_visit_satisfied, true, not_canceled)).
test("exclusion - skydiving", not_covered_by_policy(hospitalization_due_to_skydiving)).
test("coverage - hospitalization anywhere in the world", covered_by_policy(hospitalization_due_to_accidental_injury, "London", 75)).
test("cancellation - late wellness visit", policy_in_effect(signed_agreement, true, premium_paid, true, wellness_visit_satisfied, false, not_canceled)).
test("exclusion - age greater than 80", not_covered_by_policy(hospitalization_due_to_sickness, 85)).
