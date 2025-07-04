% This rule defines that a claim is covered if the policy is in effect at the time of hospitalization.
covered_by_policy(Claim) :-
    policy_in_effect(Claim).

% This rule defines the conditions under which the policy is considered in effect at the time of hospitalization.
policy_in_effect(Claim) :-
    claim_hospitalization_date(Claim, HospitalizationDate),
    policy_effective_date(EffectiveDate),
    % We assume the policy is in effect if the hospitalization date is on or after the effective date.
    HospitalizationDate >= EffectiveDate,
    policy_canceled(Claim, HospitalizationDate).

% This rule defines when the policy is considered not canceled at a specific date.
% It is not canceled if none of the cancellation conditions are met by that date.
policy_canceled(Claim, Date) :-
    \+ (policy_canceled(Claim, Date)).

% This rule defines the conditions under which the policy is considered canceled at a specific date.
policy_canceled(Claim, Date) :-
    (   claim_involves_fraud(Claim)
    ;   claim_involves_misrepresentation(Claim)
    ;   claim_involves_material_withholding(Claim)
    ).
policy_canceled(Claim, Date) :-
    policy_effective_date(EffectiveDate),
    % Cancellation due to late wellness visit confirmation
    % If the wellness visit confirmation is due by the 6th month anniversary and not satisfied in a timely fashion,
    % and the current date is after the 7th month anniversary.
    % The 'timely fashion' implies the wellness visit occurred no later than the 6th month anniversary.
    policy_effective_date(PolicyTermDuration),
    Add6Months is 6 * 30, % Approximate 30 days per month
    Add7Months is 7 * 30, % Approximate 30 days per month
    EffectiveDate + Add6Months =:= WellnessVisitDeadline,
    EffectiveDate + Add7Months =:= WellnessConfirmationDeadline,
    Date >= WellnessConfirmationDeadline,
    \+ (claim_wellness_visit_confirmation_provided_by_date(Claim, WellnessVisitDeadline)).

policy_canceled(Claim, Date) :-
    % Automatic cancellation at the end of the policy term.
    policy_effective_date(EffectiveDate),
    policy_effective_date(PolicyTermDuration),
    EffectiveDate + PolicyTermDuration =:= EndOfTermDate,
    Date >= EndOfTermDate.

% This rule defines that a claim is covered if no general exclusions apply.
covered_by_policy(Claim) :-
    policy_in_effect(Claim),
    \+ (is_exclusion_applicable(Claim)).

% This rule defines the conditions under which a general exclusion applies to a claim.
is_exclusion_applicable(Claim) :-
    claim_cause_of_sickness_or_injury(Claim, Cause),
    (   Cause = skydiving
    ;   Cause = military_service
    ;   Cause = firefighter_service
    ;   Cause = police_service
    ).
is_exclusion_applicable(Claim) :-
    claim_hospitalization_date(Claim, HospitalizationDate),
    claim_claimant_age_at_hospitalization(Claim, ClaimantAge),
    ClaimantAge >= 80.

% Assume the following are dynamic predicates that would be populated with facts for each claim.
% For example, in a query, you might assert:
% claim_hospitalization_date(claim1, date(2023, 10, 15)).
% claim_cause_of_sickness_or_injury(claim1, accidental_injury).
% claim_claimant_age_at_hospitalization(claim1, 75).
% policy_effective_date(date(2023, 1, 1)).
% policy_effective_date(365). % In days
% claim_wellness_visit_confirmation_provided_by_date(claim1, date(2023, 7, 1)).

% Predicates to define the policy's effective date and term duration.
% These are assumed to be facts asserted externally for a given policy instance.
% Example: policy_effective_date(date(2023, 1, 1)).
% Example: policy_effective_date(365). % duration in days

% Predicates related to claim details. These are assumed to be facts asserted externally for each claim.
% Example: claim_hospitalization_date(Claim, Date).
% Example: claim_cause_of_sickness_or_injury(Claim, Cause).
% Cause can be sickness or accidental_injury.
% Example: claim_claimant_age_at_hospitalization(Claim, Age).
% Example: claim_involves_fraud(Claim).
% Example: claim_involves_misrepresentation(Claim).
% Example: claim_involves_material_withholding(Claim).
% Example: claim_wellness_visit_confirmation_provided_by_date(Claim, Date).

% Helper predicates to represent policy parameters.
% These are assumed to be facts asserted externally for a given policy instance.
% The effective date is the reference point for all date calculations.
% Example: policy_effective_date(date(2023, 1, 1)).

% The policy term is 1 year from the effective date.
% Example: policy_effective_date(365). % Represents one year in days for calculation purposes.

% The wellness visit must occur no later than the 6th month anniversary of the effective date.
% This is represented by a deadline date relative to the effective date.
% The confirmation must be supplied no later than the 7th month anniversary.
% Example:
% wellness_visit_deadline_relative_to_effective_date(180). % Approximately 6 months
% wellness_confirmation_deadline_relative_to_effective_date(210). % Approximately 7 months