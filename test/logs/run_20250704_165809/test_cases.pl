test("Policy in effect: signed and premium paid",
    policy_in_effect(signed, premium_paid, condition_satisfied, not_canceled)).
test("Cancellation due to fraud",
    policy_in_effect(signed, premium_paid, condition_satisfied, canceled(fraud))).
test("Coverage exclusion: skydiving injury",
    is_claim_covered(injury_due_to(skydiving), PolicyDetails, Benefit)).
test("Coverage exclusion: age 80 or older",
    is_claim_covered(hospitalization_due_to(sickness), PolicyDetailsWithAge80, Benefit)).
test("Condition precedent: wellness visit not timely",
    policy_in_effect(signed, premium_paid, condition_not_satisfied, not_canceled)).
test("policy in effect with all conditions met",
    policy_in_effect("sickness_x", date(2023, 5, 15))
).
test("coverage excluded due to age",
    not(covers_hospitalization("accident_y", date(2023, 7, 1), 85))
).
test("coverage excluded due to military service",
    not(covers_hospitalization("sickness_z", date(2023, 8, 10), 50))
).
test("policy not in effect due to unpaid premium",
    not(policy_in_effect("sickness_a", date(2023, 9, 20)))
).
test("policy not in effect due to missed wellness visit confirmation",
    not(policy_in_effect("accident_b", date(2023, 10, 1)))
).
