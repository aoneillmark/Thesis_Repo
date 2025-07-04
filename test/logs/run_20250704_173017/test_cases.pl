test("wellness visit within 6 months",
    covered_by_policy(Scenario, Policy),
    Policy = chubb_hospital_cash_benefit,
    Scenario = hospitalization_for_sickness(date_relative_to_effective_date(5_months))
).
test("exclusion for skydiving injury",
    not(covered_by_policy(Scenario, Policy)),
    Policy = chubb_hospital_cash_benefit,
    Scenario = hospitalization_for_accidental_injury(date_relative_to_effective_date(8_months), Cause=skydiving)
).
test("coverage outside US",
    covered_by_policy(Scenario, Policy),
    Policy = chubb_hospital_cash_benefit,
    Scenario = hospitalization_for_sickness(date_relative_to_effective_date(1_month), Location="Germany")
).
test("age exclusion at hospitalization",
    not(covered_by_policy(Scenario, Policy)),
    Policy = chubb_hospital_cash_benefit,
    Scenario = hospitalization_for_sickness(date_relative_to_effective_date(10_months), ClaimantAge=82)
).
test("arbitration condition for dispute",
    covered_by_policy(Scenario, Policy),
    Policy = chubb_hospital_cash_benefit,
    Scenario = dispute_regarding_claim(date_relative_to_effective_date(9_months))
).
test("wellness_visit_timely", "policy_covered(ClaimDate, ClaimantAge, hospitalization(wellness_visit_timely_condition_met)).
test("exclusion_skydiving", "policy_covered(ClaimDate, ClaimantAge, hospitalization(skydiving_activity)).
test("age_exclusion_above_80", "policy_covered(ClaimDate, ClaimantAge, hospitalization(injury_at_age_80)).
test("world_wide_coverage", "policy_covered(ClaimDate, ClaimantAge, hospitalization(location_coverage, 'USA')).
test("arbitration_timeframe", "policy_covered(ClaimDate, ClaimantAge, hospitalization(arbitration_commenced_within_3_months)).
