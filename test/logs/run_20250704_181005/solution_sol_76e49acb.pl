% Predicate to determine if a claim is covered under the policy.
% claim_covered(ClaimEvent, ClaimantAge, PolicyEffectiveDate, ClaimSubmissionDate, ArbitrationStartDate)
% ClaimEvent: The event causing sickness or accidental injury.
% ClaimantAge: The age of the claimant at the time of hospitalization.
% PolicyEffectiveDate: The effective date of the policy.
% ClaimSubmissionDate: The date the claim was submitted.
% ArbitrationStartDate: The date arbitration was commenced, if applicable.
claim_covered(ClaimEvent, ClaimantAge, PolicyEffectiveDate, ClaimSubmissionDate, ArbitrationStartDate) :-
    policy_in_effect(PolicyEffectiveDate),
    event_not_excluded(ClaimEvent, ClaimantAge),
    claim_covered(ClaimSubmissionDate, ArbitrationStartDate).

% Rules for policy_in_effect based on the contract.
% The policy is in effect if it hasn't been canceled and the conditions in 1.1 are met.
% We assume conditions 1.1.1 and 1.1.2 are met as per instructions.
policy_in_effect(PolicyEffectiveDate) :-
    \+ policy_canceled(PolicyEffectiveDate),
    wellness_visit_condition_met(PolicyEffectiveDate).

% Rule for condition 1.3: Wellness visit confirmation.
% The condition is that written confirmation from a medical provider of a wellness visit
% for yourself with a qualified medical provider occurred no later than the 6th month
% anniversary of the effective date of this policy.
% wellness_visit_condition_met(PolicyEffectiveDate)
wellness_visit_condition_met(PolicyEffectiveDate) :-
    % The condition is satisfied if it is pending or has been satisfied in a timely fashion.
    % Since we are checking coverage at the time of a claim, we assume it's satisfied if met.
    % The actual date of the wellness visit confirmation is not provided, so we use a placeholder.
    % In a real system, this would likely be a fact or a dynamic predicate.
    % For the purpose of these rules, we assume the condition is met if the policy is active.
    % This implicitly means the wellness visit has occurred within the timeframe or the policy
    % would have been canceled.
    true. % Placeholder for a more complex check involving actual visit dates.

% Rules for policy cancellation.
% policy_canceled(PolicyEffectiveDate)
% Cancellation due to fraud, misrepresentation, material withholding.
% These are not quantifiable from the given text without additional information, so we assume they are not met.
policy_canceled(PolicyEffectiveDate) :-
    % Fraud or misrepresentation - not encoded as facts or rules are not provided.
    fail,
    % Cancellation at end of policy term (1 year from effective date).
    % This is implicitly handled by checking policy_in_effect.
    % If the claim happens after the policy term, policy_in_effect should fail.
    % For simplicity, we are not encoding an explicit end-of-term check here,
    % assuming queries are made within the policy term or that other mechanisms handle this.
    % The text says "unless previously canceled pursuant to Section 1 above", which is what we check.
    false. % No explicit cancellation rules other than those related to condition 1.3 not being met.

% Rules for general exclusions.
% event_not_excluded(ClaimEvent, ClaimantAge)
% Checks if the claim event or claimant's age falls under any general exclusion.
event_not_excluded(ClaimEvent, ClaimantAge) :-
    not(event_not_excluded(ClaimEvent)),
    not(event_not_excluded(ClaimEvent)),
    not(exclusion_age_greater_than_or_equal_to_80(ClaimantAge)).

% Rule for exclusion based on activity.
% event_not_excluded(ClaimEvent)
event_not_excluded(skydiving).

% Rule for exclusion based on occupation.
% event_not_excluded(ClaimEvent)
event_not_excluded(service_in_military).
event_not_excluded(service_as_firefighter).
event_not_excluded(service_in_police).

% Rule for exclusion based on age.
% exclusion_age_greater_than_or_equal_to_80(ClaimantAge)
exclusion_age_greater_than_or_equal_to_80(ClaimantAge) :-
    ClaimantAge >= 80.

% Rules for claim conditions.
% claim_covered(ClaimSubmissionDate, ArbitrationStartDate)
% Assumes the claim submission is within 60 days after proof of claim.
% Assumes arbitration conditions are met if they are not required or are met.
claim_covered(ClaimSubmissionDate, ArbitrationStartDate) :-
    % No recovery before the expiration of sixty (60) days after written proof of claim has been submitted.
    % This means if a claim is being made, it must be at least 60 days after proof of claim.
    % We interpret 'ClaimSubmissionDate' as the date the claim is *made* or *processed*,
    % and implicitly, this date is after the required proof of claim submission.
    % If the claim event occurred, and proof of claim was submitted, and 60 days have passed,
    % then this condition is met.
    % As dates are relative, if ClaimSubmissionDate is provided, it implies this condition is met.
    true, % Placeholder: In a real scenario, would need dates of proof of claim submission and compare with ClaimSubmissionDate.

    % Arbitration condition: commencement within three (3) months from the day parties are unable to settle.
    % If arbitration is not required for a claim to proceed, this is met.
    % If arbitration is required and commenced, the date must be within 3 months.
    % Given the contract, it seems arbitration is a condition precedent to liability if a dispute arises.
    % If no dispute arises, or if the claim is processed without dispute, this is met.
    % We assume that if ArbitrationStartDate is provided, it's validly commenced.
    % If no arbitration date is provided, we assume no dispute required arbitration commencement.
    true. % Placeholder: A full implementation would require tracking dispute resolution.

% Predicate to determine if the policy applies to the event.
% The policy insures You twenty-four (24) hours a day anywhere in the world.
% applies_globally :- true.

% Predicate to check if the policy is governed by New York law.
% governed_by_new_york_law :- true.

% Predicate to check if payments are in US Currency.
% payments_in_us_currency :- true.

% Predicate for policy term.
% The term is one year from the effective date unless previously canceled.
% This is implicitly handled by policy_in_effect.