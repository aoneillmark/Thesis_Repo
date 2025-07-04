% Rule to determine if the policy is in effect.
% The policy is in effect if it's not canceled and the wellness visit condition is pending or satisfied.
% Assumes agreement signed and premium paid as per instructions.
policy_in_effect(EffectiveDate) :-
    not(policy_canceled(EffectiveDate)),
    (   wellness_visit_satisfied(EffectiveDate)
    ;   wellness_visit_satisfied(EffectiveDate)
    ).

% Rule to determine if the policy has been canceled.
% Cancellation occurs due to fraud, misrepresentation, material withholding,
% or if the wellness visit condition is not satisfied timely.
% Also canceled at the end of the policy term.
policy_canceled(EffectiveDate) :-
    % Fraud, misrepresentation, or material withholding implies cancellation.
    % This is a simplification as these conditions would typically be determined by external facts not represented here.
    % For the purpose of this exercise, we'll consider them as events that would lead to cancellation.
    % In a real system, these would be facts provided in a query.
    % For this exercise, we'll treat them as conditions that *could* lead to cancellation if asserted as facts.
    (   fraudulent_act_occurred
    ;   misrepresentation_occurred
    ;   material_withholding_occurred
    ),
    % If any of these are true, the policy is considered canceled.
    % We will not define facts for these here as per instructions, but the rule accounts for them.
    true. % Placeholder to ensure the rule can be evaluated

policy_canceled(EffectiveDate) :-
    % Policy is automatically canceled at the end of the policy term.
    % Policy term is one year from the effective date.
    policy_term_end_date(EffectiveDate, TermEndDate),
    % In a query, the current date relative to EffectiveDate would be passed.
    % For this encoding, we represent the condition of being at or after the end of the term.
    % A query would check if the claim date is after TermEndDate.
    true. % Placeholder to represent the condition of being at or after the end of the term.

% Rule to check if the wellness visit condition is pending.
% The wellness visit should occur no later than the 6th month anniversary of the effective date.
% This rule is true if the claim date is before or on the 6th month anniversary.
wellness_visit_satisfied(EffectiveDate) :-
    % In a query, ClaimDate would be provided.
    % The condition is that the wellness visit must happen by the 6th month.
    % If a claim is made *before* or *on* the 6th month anniversary, the condition is still pending.
    % We assume a claim date is provided implicitly in the query context for coverage checks.
    true. % Placeholder, actual check would involve comparing claim date to effective date + 6 months.

% Rule to check if the wellness visit condition has been satisfied in a timely fashion.
% The wellness visit must occur no later than the 6th month anniversary of the effective date.
% This rule is true if the wellness visit occurred by the 6th month anniversary.
wellness_visit_satisfied(EffectiveDate) :-
    % In a query, a fact like 'wellness_visit_occurred_by_6th_month_anniversary' would be asserted.
    % We will not define facts for this here as per instructions.
    true. % Placeholder to represent the condition being met.

% Rule to check if a claim is covered under the policy.
% A claim is covered if the policy is in effect at the time of hospitalization.
% And the cause of sickness or accidental injury is not excluded.
% And the claimant's age is less than 80 at the time of hospitalization.
claim_covered(EffectiveDate, ClaimantAge, CauseOfInjury) :-
    policy_in_effect(EffectiveDate),
    not(is_excluded_cause(CauseOfInjury)),
    claimant_age_within_limit(ClaimantAge).

% Rule to determine if a cause of injury is excluded.
% Excludes skydiving, military service, firefighter service, police service.
is_excluded_cause(skydiving).
is_excluded_cause(military_service).
is_excluded_cause(firefighter_service).
is_excluded_cause(police_service).

% Rule to check if the claimant's age at hospitalization is within the policy limit.
% The policy does not apply if age is 80 or greater.
claimant_age_within_limit(Age) :-
    Age < 80.

% Helper rule to define the end of the policy term.
% Policy term is one year from the effective date.
policy_term_end_date(EffectiveDate, TermEndDate) :-
    % This rule would calculate TermEndDate by adding one year to EffectiveDate.
    % As dates are relative, and the specific date arithmetic is not required for Prolog logic here,
    % we represent this as a rule that would yield the end date if the effective date were provided.
    % For example, if EffectiveDate is Jan 1, 2023, TermEndDate is Jan 1, 2024.
    % A query would involve comparing a claim date to this TermEndDate.
    true. % Placeholder for date calculation logic.

% Dynamic predicates for conditions that would typically be asserted as facts.
% As per instructions, we will not define facts, but these predicates represent
% conditions that, if true, would affect policy status or coverage.
% These are declared here to ensure they are known to the Prolog system,
% even though no facts will be asserted for them in this output.
:- dynamic fraudulent_act_occurred/0.
:- dynamic misrepresentation_occurred/0.
:- dynamic material_withholding_occurred/0.
% This predicate would typically be asserted if a wellness visit occurred by the 6th month.
:- dynamic wellness_visit_occurred_by_6th_month_anniversary/0.