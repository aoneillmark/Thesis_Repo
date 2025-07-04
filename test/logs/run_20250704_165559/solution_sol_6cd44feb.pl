% Rule: policy_in_effect(EffectiveDate)
% Explains that the policy is considered in effect if all the necessary conditions for its validity are met.
policy_in_effect(EffectiveDate) :-
    agreement_signed(EffectiveDate),
    premium_paid(EffectiveDate),
    wellness_visit_condition_met(EffectiveDate),
    policy_not_canceled(EffectiveDate).

% Rule: agreement_signed(EffectiveDate)
% Declares that the agreement is considered signed, as per the problem statement's assumptions.
agreement_signed(EffectiveDate).

% Rule: premium_paid(EffectiveDate)
% Declares that the premium is considered paid, as per the problem statement's assumptions.
premium_paid(EffectiveDate).

% Rule: wellness_visit_condition_met(EffectiveDate)
% Defines the condition that the wellness visit confirmation must be supplied within the specified timeframe relative to the effective date.
% This rule states the condition is met if it's either still pending or has been satisfied on time.
% For the purpose of coverage assessment, we'll assume "pending or satisfied in a timely fashion" implies the condition is met for policy effectiveness.
wellness_visit_condition_met(EffectiveDate).

% Rule: policy_not_canceled(EffectiveDate)
% Checks if the policy has not been canceled.
% This is true if none of the cancellation conditions are met.
policy_not_canceled(EffectiveDate) :-
    \+ has_fraud_or_misrepresentation(EffectiveDate),
    \+ wellness_visit_condition_not_satisfied_timely(EffectiveDate),
    \+ policy_not_canceled(EffectiveDate).

% Rule: has_fraud_or_misrepresentation(EffectiveDate)
% Placeholder for fraud or misrepresentation. Assumed false for general coverage checks unless specified.
% In a real system, this would likely involve dynamic facts asserting fraud.
has_fraud_or_misrepresentation(EffectiveDate).

% Rule: wellness_visit_condition_not_satisfied_timely(EffectiveDate)
% This rule checks if the wellness visit condition was NOT satisfied in a timely fashion.
% The condition is satisfied on time if confirmation is supplied no later than the 6th month anniversary of the effective date.
% This rule being true means cancellation due to this condition.
% For coverage assessment, we consider this condition 'not satisfied timely' if it's not true that a wellness visit occurred by the 6th month anniversary.
wellness_visit_condition_not_satisfied_timely(EffectiveDate) :-
    \+ wellness_visit_date(EffectiveDate).

% Rule: wellness_visit_date(EffectiveDate)
% Assumed true for general coverage checks as per problem statement's assumptions implicitly covering this.
% In a real system, this would be a fact asserted for a specific policy.
wellness_visit_date(EffectiveDate).

% Rule: policy_not_canceled(EffectiveDate)
% Checks if the policy has been canceled due to reaching the end of its term.
% The policy term is one year from the effective date.
% This rule is true if the current time (implicit in the query context) is past the end of the term.
% For this implementation, we'll assume any query about coverage implies the policy is within its term or we're checking eligibility before the term ends.
% This predicate is defined for completeness but isn't actively used to deny coverage in the current coverage_eligible rule as it's assumed the query is for an active period.
policy_not_canceled(EffectiveDate) :-
    % This predicate would be true if the current date relative to EffectiveDate is past the 1 year term.
    % For example: current_date_relative_to_effective_date > 365.
    % Given the assumption of relative dates, we'll let the query context manage this.
    fail. % By default, assume not canceled at end of term for coverage checks.

% Rule: claim_covered(ClaimType, ClaimantAge, DateOfHospitalization)
% Determines if a specific claim is covered under the policy.
% It requires the policy to be in effect and no general exclusions to apply to the claim event.
claim_covered(ClaimType, ClaimantAge, DateOfHospitalization) :-
    policy_in_effect(EffectiveDate), % Checks if the policy is active and valid.
    \+ exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization), % Checks if any exclusion negates coverage.
    (ClaimType == sickness ; ClaimType == accidental_injury). % Ensures the claim is for sickness or accidental injury.

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Checks if any of the general exclusions listed in section 2.1 apply to the claim.
exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization) :-
    exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization);
    exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization);
    exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization);
    exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization);
    exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization).

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Exclusion for claims arising from skydiving.
exclusion_applies(skydiving_related, _, _).

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Exclusion for claims arising from service in the military.
exclusion_applies(military_service_related, _, _).

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Exclusion for claims arising from service as a firefighter.
exclusion_applies(firefighter_service_related, _, _).

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Exclusion for claims arising from service in the police.
exclusion_applies(police_service_related, _, _).

% Rule: exclusion_applies(ClaimType, ClaimantAge, DateOfHospitalization)
% Exclusion for claims where the claimant's age at hospitalization is 80 or older.
exclusion_applies(_, ClaimantAge, _) :-
    ClaimantAge >= 80.

% Rule: policy_applies_worldwide(EffectiveDate)
% States that the policy applies anywhere in the world, 24 hours a day.
policy_applies_worldwide(EffectiveDate).

% Rule: law_of_new_york_governs(EffectiveDate)
% States that the policy is governed by the laws of New York.
law_of_new_york_governs(EffectiveDate).

% Rule: all_payments_in_usd(EffectiveDate)
% States that all payments under the policy must be in United States currency.
all_payments_in_usd(EffectiveDate).

% Rule: policy_term_duration_one_year(EffectiveDate)
% Defines the policy term as one year from the effective date, unless canceled.
policy_term_duration_one_year(EffectiveDate).