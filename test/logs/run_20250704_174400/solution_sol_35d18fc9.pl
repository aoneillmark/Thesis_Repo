% Predicates for defining policy terms and conditions.

% policy_in_effect(EffectiveDate, TodayDate, PolicyTermEndDate, WellnessVisitConfirmationDate, PolicyCanceled)
% This rule defines the conditions under which the policy is considered in effect.
% It assumes the agreement is signed and premiums are paid (as per instructions).
policy_in_effect(EffectiveDate, TodayDate, PolicyTermEndDate, WellnessVisitConfirmationDate, PolicyCanceled) :-
    % The policy must not be canceled.
    \+ policy_canceled(EffectiveDate, TodayDate, PolicyTermEndDate),
    % The condition in Section 1.3 must be satisfied.
    section_1_3_satisfied(EffectiveDate, WellnessVisitConfirmationDate).

% section_1_3_satisfied(EffectiveDate, WellnessVisitConfirmationDate)
% This rule checks if the wellness visit condition is satisfied.
% The wellness visit confirmation must be provided no later than the 6th month anniversary of the effective date.
section_1_3_satisfied(EffectiveDate, WellnessVisitConfirmationDate) :-
    % Assuming dates are represented as numbers of months from the effective date.
    WellnessVisitConfirmationDate =< 6.

% policy_canceled(EffectiveDate, TodayDate, PolicyTermEndDate)
% This rule defines the conditions under which the policy is considered canceled.
policy_canceled(EffectiveDate, TodayDate, PolicyTermEndDate) :-
    % Cancellation due to fraud or misrepresentation (not directly representable without specific facts/states).
    % For the purpose of this encoding, we assume such events would lead to a 'true' value for this predicate.
    % However, as per instructions, we are defining rules, not facts. Thus, we leave this case implicit,
    % assuming if fraud/misrepresentation occurred, a query would reflect it as a cancellation.

    % Automatic cancellation at the end of the policy term.
    TodayDate >= PolicyTermEndDate.

% claim_covered(EffectiveDate, HospitalizationDate, HospitalizationEndDate, ClaimantAgeAtHospitalization, PolicyTermEndDate, WellnessVisitConfirmationDate, PolicyCanceled)
% This is the main predicate to determine if a claim for hospitalization is covered.
claim_covered(EffectiveDate, HospitalizationDate, HospitalizationEndDate, ClaimantAgeAtHospitalization, PolicyTermEndDate, WellnessVisitConfirmationDate, PolicyCanceled) :-
    % The policy must be in effect at the time of hospitalization.
    % We are assuming HospitalizationDate is relative to the EffectiveDate, and policy is in effect for the duration of hospitalization.
    % Since we only have an effective date and a policy term end date, we assume the hospitalization date falls within the policy term.
    policy_in_effect(EffectiveDate, HospitalizationDate, PolicyTermEndDate, WellnessVisitConfirmationDate, PolicyCanceled),
    % The claim must not fall under any general exclusions.
    \+ is_excluded_cause(HospitalizationDate, ClaimantAgeAtHospitalization).

% is_excluded_cause(HospitalizationDate, ClaimantAgeAtHospitalization)
% This rule checks if any of the general exclusions apply to a claim.
is_excluded_cause(_HospitalizationDate, ClaimantAgeAtHospitalization) :-
    % Exclusion 2.1.1: Skydiving.
    % This would typically be a fact about the cause of hospitalization.
    % As we are only defining rules, we assume if the cause was skydiving, this would evaluate to true.
    % However, without causal information, this part of exclusion cannot be directly encoded as a rule.

    % Exclusion 2.1.2: Service in the military.
    % Similar to skydiving, requires information about the cause.

    % Exclusion 2.1.3: Service as a fire fighter.
    % Similar to skydiving, requires information about the cause.

    % Exclusion 2.1.4: Service in the police.
    % Similar to skydiving, requires information about the cause.

    % Exclusion 2.1.5: Age at hospitalization is 80 or greater.
    ClaimantAgeAtHospitalization >= 80.

% --- Helper predicates for date comparisons (relative to effective date) ---
% These are conceptual and would require a specific date representation if actual dates were used.
% For simplicity, we assume dates are represented as a numerical value (e.g., months from effective date).

% Example representation: if effective date is month 0, then 6th month anniversary is month 6.

% Note: Section 1.2 mentions "midnight, US Eastern time then in effect, on the last day of the policy term".
% Our representation of PolicyTermEndDate already signifies this boundary.
% Section 3.2.1 mentions periods for arbitration and claim submission after proof of claim.
% These are conditions for dispute resolution and recovery, not directly for initial claim coverage determination based on policy terms,
% and are thus omitted from the core `is_claim_covered` logic as per the focus on policy coverage.
% Section 3.3.1 specifies the governing law (New York), which doesn't translate into a Prolog rule for coverage.
% Section 3.4.1 specifies currency, also not a coverage rule.
% Section 3.5.1 states lump sum premium payment at signing, which is assumed true as per instructions.
% Section 3.6.1 defines policy term as one year from the effective date, which is used in PolicyTermEndDate.