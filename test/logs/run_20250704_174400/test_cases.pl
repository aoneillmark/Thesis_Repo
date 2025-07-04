test("wellness_visit_within_6_months", policy_covers_hospitalization(WellnessVisitDate, HospitalizationDate, InjuryType) :-
    WellnessVisitDate = 5_months_after_effective_date,
    HospitalizationDate = 7_months_after_effective_date,
    InjuryType = accidental_injury,
    \+ excluded(WellnessVisitDate, HospitalizationDate, InjuryType)).
test("wellness_visit_after_6_months", policy_covers_hospitalization(WellnessVisitDate, HospitalizationDate, InjuryType) :-
    WellnessVisitDate = 7_months_after_effective_date,
    HospitalizationDate = 8_months_after_effective_date,
    InjuryType = sickness,
    excluded(WellnessVisitDate, HospitalizationDate, InjuryType)).
test("age_exclusion_at_hospitalization", policy_covers_hospitalization(WellnessVisitDate, HospitalizationDate, InjuryType) :-
    WellnessVisitDate = 3_months_after_effective_date,
    HospitalizationDate = 5_months_after_effective_date,
    InjuryType = accidental_injury,
    ClaimantAgeAtHospitalization = 80,
    excluded(WellnessVisitDate, HospitalizationDate, InjuryType)).
test("skydiving_exclusion", policy_covers_hospitalization(WellnessVisitDate, HospitalizationDate, InjuryType) :-
    WellnessVisitDate = 2_months_after_effective_date,
    HospitalizationDate = 4_months_after_effective_date,
    InjuryType = skydiving_related_injury,
    excluded(WellnessVisitDate, HospitalizationDate, InjuryType)).
test("global_coverage", policy_covers_hospitalization(WellnessVisitDate, HospitalizationDate, InjuryType) :-
    WellnessVisitDate = 1_month_after_effective_date,
    HospitalizationDate = 3_months_after_effective_date,
    Location = "Germany",
    InjuryType = sickness,
    \+ excluded(WellnessVisitDate, HospitalizationDate, InjuryType)).
test("covered_wellness_visit_within_timeframe",
    hospitalization_covered(
        policy_effective_date(date(2023, 1, 1)),
        hospitalization_date(date(2023, 6, 15)),
        wellness_visit_date(date(2023, 5, 1)),
        claimant_age_at_hospitalization(55)
    )
).
test("excluded_skydiving_injury",
    \+ hospitalization_covered(
        policy_effective_date(date(2023, 1, 1)),
        hospitalization_date(date(2023, 7, 1)),
        wellness_visit_date(date(2023, 3, 15)),
        claimant_age_at_hospitalization(40),
        cause_of_injury(skydiving)
    )
).
test("excluded_age_over_80",
    \+ hospitalization_covered(
        policy_effective_date(date(2023, 1, 1)),
        hospitalization_date(date(2023, 9, 1)),
        wellness_visit_date(date(2023, 4, 1)),
        claimant_age_at_hospitalization(81)
    )
).
test("covered_military_service_not_cause_of_injury",
    hospitalization_covered(
        policy_effective_date(date(2023, 1, 1)),
        hospitalization_date(date(2023, 10, 1)),
        wellness_visit_date(date(2023, 5, 10)),
        claimant_age_at_hospitalization(60),
        service_status(military),
        cause_of_injury(common_flu)
    )
).
test("excluded_wellness_visit_after_timeframe",
    \+ hospitalization_covered(
        policy_effective_date(date(2023, 1, 1)),
        hospitalization_date(date(2023, 8, 1)),
        wellness_visit_date(date(2023, 7, 15)),
        claimant_age_at_hospitalization(50)
    )
).
