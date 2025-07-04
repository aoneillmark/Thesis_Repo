% Rule: policy_in_effect(EffectiveDate, CancellationDate, HasWellnessVisitConfirmation, WellnessVisitDateLimit)
% This rule defines the conditions under which the insurance policy is considered to be in effect.
% It checks if the policy has not been canceled, if a wellness visit confirmation has been provided by a certain date,
% and if the policy is within its effective term.
policy_in_effect(EffectiveDate, CancellationDate, HasWellnessVisitConfirmation, WellnessVisitDateLimit) :-
    % The policy is in effect if it has not been canceled.
    % We assume here that CancellationDate is unbound or a date far in the future if not canceled.
    % For simplicity, we rely on a condition that implies cancellation did not happen.
    % The condition "policy has not been canceled" from the text is implicitly handled by the fact
    % that if cancellation occurred, we wouldn't be evaluating policy_in_effect in this context.
    % We'll use a variable that is true if not canceled.
    policy_not_canceled(EffectiveDate, CancellationDate),

    % The condition set out in Section 1.3 must be pending or satisfied in a timely fashion.
    % This means the wellness visit confirmation must be provided by the 7th month anniversary.
    % The wellness visit itself must occur no later than the 6th month anniversary.
    % We represent "pending or satisfied in a timely fashion" by checking if the wellness visit occurred by the deadline.
    ( HasWellnessVisitConfirmation == true ; % Assume confirmation is provided if the condition is met.
      (WellnessVisitDateLimit =< 7*30, % Assuming 30 days per month for simplicity in relative date calculation.
       WellnessVisitDateLimit >= 0) % The wellness visit must have occurred.
    ),

    % The policy is in effect if all other conditions are met.
    % Note: Payment of premium and signing of agreement are assumed true based on instructions.
    true.

% Rule: policy_not_canceled(EffectiveDate, CancellationDate)
% This rule determines if the policy has not been canceled.
% Cancellation can occur due to fraud, misrepresentation, withholding information,
% or failure to meet wellness visit requirements in a timely fashion, or reaching the end of the policy term.
% Based on the instructions, we only consider cancellation due to time.
policy_not_canceled(EffectiveDate, CancellationDate) :-
    % The policy is not canceled if a specific cancellation date is not set or is in the future.
    % In this Prolog encoding, we represent the absence of cancellation by a unbound variable for CancellationDate,
    % or if CancellationDate is a future date relative to the effective date.
    % For practical query answering, if a claim is being checked, and cancellation happened,
    % the claim would not be covered due to policy not being in effect.
    % We will assume if this rule is evaluated, the policy is not canceled through fraud or misrepresentation.
    % The policy term cancellation is handled by the effective date of the claim.
    true. % Placeholder, as explicit cancellation conditions are not directly encoded for checking "not canceled".

% Rule: claim_covered(ClaimType, HospitalizationDate, ClaimantAge)
% This rule determines if a claim is covered under the policy.
% A claim is covered if the policy was in effect at the time of hospitalization,
% and the cause of hospitalization is not excluded by general exclusions.
claim_covered(ClaimType, HospitalizationDate, ClaimantAge) :-
    % The policy must be in effect at the time of hospitalization.
    % We need to define what "policy in effect at the time of hospitalization" means relative to the policy's effective date.
    % This implies checking against the policy term and cancellation.
    % For this Prolog, we assume the policy is in effect if it wasn't canceled and the hospitalization is within a reasonable timeframe relative to its start.
    % We'll use a placeholder for the effective date of the policy to check against.
    % For simplification, let's assume the effective date is the reference point for relative dates.
    % Let's assume the policy effective date is known as `PolicyEffectiveDate`.
    % The policy is in effect if it has not been canceled and is within its term.
    % The policy term is 1 year from the effective date.
    % For the purpose of claim evaluation, the policy must be in effect on `HospitalizationDate`.
    % This implies `HospitalizationDate` must be within the policy term and no cancellation has occurred.

    % We need to check if the policy was in effect at the time of hospitalization.
    % This means the hospitalization date must be on or after the effective date
    % and on or before the end of the policy term (1 year after effective date),
    % and the policy has not been canceled before the hospitalization.
    % Given the instructions, dates are relative to the effective date.
    % Let's assume PolicyEffectiveDate is our reference.
    % So, hospitalization is within policy term if HospitalizationDate is <= 1 year relative to PolicyEffectiveDate.
    % And, hospitalization is on or after PolicyEffectiveDate.
    % The prompt states "all dates/times in any query to this code ... will be given RELATIVE to the effective date of the policy".
    % So, `HospitalizationDate` will be given as a number of days/months relative to the effective date.
    % Let's assume `HospitalizationDateRel` represents the hospitalization date relative to the policy effective date in months.
    % PolicyEffectiveDate is the reference, so a date relative to it means, e.g., 3 for 3 months after.

    % The policy is in effect on HospitalizationDate if:
    % 1. HospitalizationDate is on or after the effective date (relative date >= 0)
    % 2. HospitalizationDate is no later than the policy term end (relative date <= 12 months)
    % 3. Policy has not been canceled before HospitalizationDate.
    % Assuming `HospitalizationDateRel` is a number of months from the effective date.
    % We also need to consider the wellness visit condition. If it's not met by the 7th month, the policy is canceled.

    % Let's assume the hospitalization date is provided as a number of months relative to the effective date: `HospitalizationDateRelMonths`.
    % And the claimant's age at hospitalization is `ClaimantAge`.

    % Condition from 1.1: Policy in effect at the time of hospitalization.
    % For this, we need to consider the wellness visit condition.
    % The wellness visit must occur by the 6th month anniversary.
    % The confirmation must be supplied by the 7th month anniversary.
    % If these are not met, the policy is canceled (1.2).

    % Let's assume `HospitalizationDateRelMonths` and `WellnessVisitDateRelMonths` and `WellnessVisitConfirmationDateRelMonths` are provided for a query.
    % For policy to be in effect at hospitalization:
    % Wellness visit must have happened by 6 months relative to effective date.
    % Wellness confirmation must have been supplied by 7 months relative to effective date.
    % Hospitalization must be within the 1-year policy term.

    % Let's use placeholders for these relative dates for the rules.
    % For a query, you'd provide actual values.

    % The policy being in effect at the time of hospitalization means:
    % The hospitalization must occur within the policy term (1 year from effective date)
    % And the policy has not been canceled.
    % Cancellation can occur if the wellness visit condition (1.3) is not met timely.
    % Wellness visit by 6th month, confirmation by 7th month.
    % If wellness visit confirmation is not provided by 7th month, policy is canceled.

    % Let's refine the definition of policy_in_effect for the context of a claim.
    % Assume policy_effective_date is the reference point.
    % Policy is in effect on HospitalizationDate if:
    % 1. Wellness visit occurred by 6 months relative to effective date.
    % 2. Wellness visit confirmation provided by 7 months relative to effective date.
    % 3. HospitalizationDate is within policy term (0 to 12 months relative to effective date).
    % 4. Policy not canceled due to fraud etc. (assumed true for query).

    % Let's redefine our predicates to take relative dates in months.
    % claim_covered(ClaimType, HospitalizationDateRelMonths, ClaimantAge, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)

    % First, check if the policy was in effect at the time of hospitalization.
    policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths),

    % Then, check if any general exclusions apply.
    % General exclusions apply based on the cause of sickness/injury and claimant's age.
    % We need to associate ClaimType with a cause of sickness/injury.
    % For simplicity, let's assume ClaimType directly represents the cause that might be excluded.
    is_excluded(is_excluded(ClaimType, ClaimantAge)).

% Rule: policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)
% This rule checks if the policy was in effect on the specific hospitalization date.
% It incorporates the wellness visit conditions and the policy term.
policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths) :-
    % The policy term is one year (12 months) from the effective date.
    % The hospitalization must be within this term.
    HospitalizationDateRelMonths >= 0,
    HospitalizationDateRelMonths =< 12,

    % Section 1.3: Wellness visit confirmation must be supplied by the 7th month anniversary.
    % This means the confirmation date must be no later than the 7th month.
    % The rule in 1.1 states "condition set out in Section 1.3 is still pending or has been satisfied in a timely fashion".
    % If confirmation is not provided by 7th month, policy is canceled by 1.2.
    % So, for policy to be in effect, confirmation must be by 7th month.
    WellnessVisitConfirmationDateRelMonths =< 7,

    % The wellness visit itself must occur no later than the 6th month anniversary.
    WellnessVisitDateRelMonths =< 6,

    % Also, the wellness visit must have occurred.
    WellnessVisitDateRelMonths >= 0, % Assuming a non-negative relative date.

    % Policy is not canceled due to these conditions.
    true.

% Rule: is_excluded(CauseOfInjury, ClaimantAge)
% This rule checks if a claim is excluded based on the cause of injury or the claimant's age at hospitalization.
is_excluded(CauseOfInjury, ClaimantAge) :-
    % Exclusion 2.1.1: Skydiving
    (CauseOfInjury = skydiving ;
     CauseOfInjury = 'skydiving'), % Allow for different string representations

    % Exclusion 2.1.2: Service in the military
    (CauseOfInjury = military_service ;
     CauseOfInjury = 'military service'),

    % Exclusion 2.1.3: Service as a fire fighter
    (CauseOfInjury = firefighter_service ;
     CauseOfInjury = 'fire fighter service'),

    % Exclusion 2.1.4: Service in the police
    (CauseOfInjury = police_service ;
     CauseOfInjury = 'police service'),

    % Exclusion 2.1.5: Age equal to or greater than 80 years.
    ClaimantAge >= 80.

% Predicate to check if a specific cause is among the excluded ones.
is_excluded(CauseOfInjury) :-
    % Exclusion 2.1.1: Skydiving
    (CauseOfInjury = skydiving ;
     CauseOfInjury = 'skydiving'),
    !. % Cut to commit to this choice if matched.

is_excluded(CauseOfInjury) :-
    % Exclusion 2.1.2: Service in the military
    (CauseOfInjury = military_service ;
     CauseOfInjury = 'military service'),
    !.

is_excluded(CauseOfInjury) :-
    % Exclusion 2.1.3: Service as a fire fighter
    (CauseOfInjury = firefighter_service ;
     CauseOfInjury = 'fire fighter service'),
    !.

is_excluded(CauseOfInjury) :-
    % Exclusion 2.1.4: Service in the police
    (CauseOfInjury = police_service ;
     CauseOfInjury = 'police service'),
    !.

% Helper rule that combines cause exclusion and age exclusion.
% This rule is used within claim_covered.
% It means if the cause is excluded OR the age is excluded, then the claim is excluded.
is_excluded(CauseOfInjury, ClaimantAge) :-
    % Check if the cause of injury is NOT one of the explicitly excluded causes.
    % If it's not in the excluded list, then it's not excluded by cause.
    % The condition for coverage is NOT (is_excluded(CauseOfInjury, ClaimantAge)).
    % So, we want to assert that it is NOT excluded.
    % This happens if there's no exclusion for the cause, OR there's no exclusion for the age.

    % We negate the is_excluded rule directly by checking its negation.
    % This is equivalent to saying:
    % A claim is NOT excluded if:
    % 1. The cause of injury is NOT any of the specifically listed excluded causes.
    % OR
    % 2. The claimant's age is LESS THAN 80.

    % Let's structure it as: claim is covered if NOT excluded.
    % NOT excluded means (NOT excluded_by_cause) AND (NOT excluded_by_age).
    % This seems more direct.

    % Condition for NOT being excluded by cause:
    % The CauseOfInjury is not in the list of excluded causes.
    % This means, if we call is_excluded(CauseOfInjury) it should fail.
    \+ is_excluded(CauseOfInjury),

    % Condition for NOT being excluded by age:
    ClaimantAge < 80.

% Redefining is_excluded to be cleaner and directly used in claim_covered.
% This means a claim is excluded if *any* of the exclusion conditions are met.
is_excluded(ClaimType, ClaimantAge) :-
    % Either the cause is excluded OR the age is too high.
    ( is_excluded(ClaimType)
    ; % OR
      ClaimantAge >= 80
    ).

% The claim_covered rule needs to be structured such that it checks if the policy is in effect AND not excluded.
% Let's rewrite claim_covered:
% claim_covered(ClaimType, HospitalizationDateRelMonths, ClaimantAge, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)

% Predicate to check if the policy was in effect on the date of hospitalization.
% This means the hospitalization date must be within the policy term, and the wellness conditions met.
% Let's assume the policy effective date is the reference point (0 months).
% Policy term is up to 12 months.
% Wellness visit by 6 months. Confirmation by 7 months.

% Rule: policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)
% This rule checks if the policy was in effect on the specific hospitalization date.
% It incorporates the wellness visit conditions and the policy term.
policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths) :-
    % Policy term is 1 year (12 months). Hospitalization must be within this term.
    HospitalizationDateRelMonths >= 0,
    HospitalizationDateRelMonths =< 12,

    % Section 1.3 requirement: Wellness visit must occur no later than the 6th month anniversary.
    WellnessVisitDateRelMonths =< 6,
    WellnessVisitDateRelMonths >= 0, % Ensure the visit occurred.

    % Section 1.1 requirement: Wellness visit confirmation from medical provider must be supplied by the 7th month anniversary.
    % Section 1.2 implies cancellation if condition in 1.3 is not satisfied timely. Timely means by 7th month for confirmation.
    WellnessVisitConfirmationDateRelMonths =< 7,
    WellnessVisitConfirmationDateRelMonths >= 0, % Ensure confirmation was provided.

    % If these conditions are met, the policy is considered in effect at the time of hospitalization.
    true.


% Final definition for claim_covered.
% claim_covered(ClaimType, HospitalizationDateRelMonths, ClaimantAge, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)
% This rule determines if a claim is covered. A claim is covered if the policy was in effect at the time of hospitalization,
% AND the claim is not excluded due to cause or age.
claim_covered(ClaimType, HospitalizationDateRelMonths, ClaimantAge, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths) :-
    % First, check if the policy was in effect at the time of hospitalization.
    policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths),

    % Second, check if the claim is NOT excluded by general exclusions (Section 2.1).
    % A claim is NOT excluded if it's not caused by skydiving, military, fire fighter, police service,
    % AND the claimant's age is less than 80.
    % This is equivalent to saying that there is NO exclusion that applies.
    % We can achieve this by checking that the 'is_excluded' predicate fails.
    \+ is_excluded(ClaimType, ClaimantAge).


% Predicate: is_excluded(CauseOfInjury, ClaimantAge)
% Checks if any exclusion condition is met for the given cause of injury and claimant's age.
% A claim is excluded if the cause of injury is one of the specific excluded types,
% OR if the claimant's age at hospitalization is 80 or older.
is_excluded(CauseOfInjury, ClaimantAge) :-
    % Check for excluded causes (Section 2.1.1 to 2.1.4)
    (CauseOfInjury = skydiving ;
     CauseOfInjury = 'skydiving' ;
     CauseOfInjury = military_service ;
     CauseOfInjury = 'military service' ;
     CauseOfInjury = firefighter_service ;
     CauseOfInjury = 'fire fighter service' ;
     CauseOfInjury = police_service ;
     CauseOfInjury = 'police service'
    ),
    % If the cause matches an exclusion, the claim is excluded.
    % We use a cut (!) to prevent backtracking to check age if a cause is matched.
    !.

is_excluded(CauseOfInjury, ClaimantAge) :-
    % Check for age exclusion (Section 2.1.5)
    ClaimantAge >= 80.

% Explanation for the predicates and rules:
% policy_in_effect(HospitalizationDateRelMonths, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)
%   - This rule defines whether the policy was active at the time of a hospitalization.
%   - It takes the hospitalization date relative to the policy's effective date (in months).
%   - It requires the hospitalization to be within the policy's one-year term (0 to 12 months relative).
%   - It enforces the condition from Section 1.3 that a wellness visit must occur by the 6th month anniversary,
%     and a confirmation of this visit must be provided by the 7th month anniversary.
%   - If these conditions are met, the policy is considered in effect for that hospitalization.

% is_excluded(CauseOfInjury, ClaimantAge)
%   - This rule checks if a claim is excluded based on general exclusions defined in Section 2.1.
%   - It takes the type of claim (representing the cause of injury) and the claimant's age at hospitalization.
%   - A claim is excluded if the CauseOfInjury is 'skydiving', 'military_service', 'firefighter_service', or 'police_service'.
%   - Additionally, a claim is excluded if the ClaimantAge is 80 or greater.
%   - The cut (!) is used to ensure that once an exclusion is matched (either by cause or age), further checks are not made for that specific claim.

% claim_covered(ClaimType, HospitalizationDateRelMonths, ClaimantAge, WellnessVisitDateRelMonths, WellnessVisitConfirmationDateRelMonths)
%   - This is the main predicate to query coverage.
%   - It takes the claim type, hospitalization date relative to the policy's effective date (in months), and the claimant's age.
%   - It also takes the wellness visit date and confirmation date relative to the policy's effective date (in months) to check policy effectiveness.
%   - A claim is covered if:
%     1. The policy was in effect at the time of hospitalization (checked by `policy_in_effect_at_hospitalization`).
%     2. The claim is NOT excluded by any of the general exclusion rules (checked by `\+ is_excluded(...)`).
%   - If both conditions are met, the predicate succeeds, indicating the claim is covered.