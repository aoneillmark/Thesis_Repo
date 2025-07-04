test("wellness_visit_satisfied_within_timeframe",
    policy_in_effect(effective_date, hospitalization_date, hospitalization_reason)
).
test("wellness_visit_not_satisfied_within_timeframe",
    \+ policy_in_effect(effective_date, hospitalization_date, hospitalization_reason)
).
test("hospitalization_due_to_skydiving_exclusion",
    \+ benefit_payable(effective_date, hospitalization_date, hospitalization_reason, claimant_age)
).
test("hospitalization_due_to_military_service_exclusion",
    \+ benefit_payable(effective_date, hospitalization_date, hospitalization_reason, claimant_age)
).
test("claimant_over_80_years_old_exclusion",
    \+ benefit_payable(effective_date, hospitalization_date, hospitalization_reason, 81)
).
test("hospitalization_covered_worldwide",
    policy_in_effect(effective_date, hospitalization_date, hospitalization_reason)
).
test("claim_within_policy_term",
    (   hospitalization_date(10_months),
        policy_effective_date(0_months),
        policy_term_years(1),
        is_covered_period(hospitalization_date, policy_effective_date, policy_term_years)
    )
).
test("wellness_visit_condition_met",
    (   wellness_visit_date(5_months),
        policy_effective_date(0_months),
        wellness_visit_required_by_months(6),
        wellness_visit_condition_satisfied(wellness_visit_date, policy_effective_date, wellness_visit_required_by_months)
    )
).
test("age_exclusion_not_met",
    (   hospitalization_date(3_months),
        claimant_age_at_hospitalization(75),
        age_exclusion_limit(80),
        not(age_is_exclusion(claimant_age_at_hospitalization, age_exclusion_limit))
    )
).
test("exclusion_for_firefighter_service",
    (   hospitalization_date(4_months),
        activity_during_hospitalization(service_as_firefighter),
        is_excluded_activity(activity_during_hospitalization)
    )
).
