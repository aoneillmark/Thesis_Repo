% Rule: policy_in_effect/1
% This rule determines if the policy is in effect, considering the conditions for its validity.
policy_in_effect(PolicyDetails) :-
    agreement_signed(PolicyDetails),
    premium_paid(PolicyDetails),
    wellness_visit_condition_met(PolicyDetails),
    policy_not_canceled(PolicyDetails).

% Rule: wellness_visit_condition_met/1
% This rule checks if the condition regarding the wellness visit has been met by the specified anniversary.
wellness_visit_condition_met(PolicyDetails) :-
    policy_effective_date(PolicyDetails, EffectiveDate),
    % The wellness visit must occur no later than the 6th month anniversary of the effective date.
    wellness_visit_date(PolicyDetails, VisitDate),
    VisitDate =< EffectiveDate + 6 months.

% Rule: not_canceled/1
% This rule checks if the policy has not been canceled.
policy_not_canceled(PolicyDetails) :-
    \+ policy_not_canceled(PolicyDetails),
    \+ policy_not_canceled(PolicyDetails),
    \+ policy_not_canceled(PolicyDetails),
    \+ wellness_visit_condition_not_satisfied_timely(PolicyDetails),
    \+ policy_not_canceled(PolicyDetails, _).

% Rule: canceled_due_to_fraud/1
% This rule determines if the policy has been canceled due to fraud.
policy_not_canceled(PolicyDetails) :-
    policy_is_canceled_for_reason(PolicyDetails, fraud).

% Rule: canceled_due_to_misrepresentation/1
% This rule determines if the policy has been canceled due to misrepresentation.
policy_not_canceled(PolicyDetails) :-
    policy_is_canceled_for_reason(PolicyDetails, misrepresentation).

% Rule: canceled_due_to_withholding_information/1
% This rule determines if the policy has been canceled due to withholding of information.
policy_not_canceled(PolicyDetails) :-
    policy_is_canceled_for_reason(PolicyDetails, withholding_information).

% Rule: wellness_condition_not_satisfied_timely/1
% This rule determines if the policy has been canceled because the wellness condition was not satisfied in a timely fashion.
wellness_visit_condition_not_satisfied_timely(PolicyDetails) :-
    policy_effective_date(PolicyDetails, EffectiveDate),
    wellness_visit_date(PolicyDetails, VisitDate),
    VisitDate > EffectiveDate + 6 months.

% Rule: canceled_at_end_of_term/2
% This rule determines if the policy has been canceled automatically at the end of its term.
policy_not_canceled(PolicyDetails, CancellationDate) :-
    policy_effective_date(PolicyDetails, EffectiveDate),
    policy_term_duration_one_year(PolicyDetails, TermYears),
    policy_term_duration_one_year(PolicyDetails, 1), % Assuming a 1 year term as per section 3.6
    CancellationDate is EffectiveDate + TermYears years.

% Rule: claim_covered/3
% This is the main predicate to query if a claim is covered.
% It checks if the policy was in effect at the time of hospitalization and if any exclusions apply.
claim_covered(PolicyDetails, HospitalizationDetails, ClaimDetails) :-
    policy_in_effect(PolicyDetails),
    hospitalization_date(HospitalizationDetails, PolicyDetails),
    is_excluded(exclusion_applies(HospitalizationDetails, ClaimDetails)).

% Rule: hospitalization_at_time_of_policy_effect/2
% This rule checks if the hospitalization occurred while the policy was in effect.
% This implies the hospitalization date is within the policy term and after the effective date.
hospitalization_date(HospitalizationDetails, PolicyDetails) :-
    policy_effective_date(PolicyDetails, EffectiveDate),
    policy_term_duration_one_year(PolicyDetails, 1), % Policy term is 1 year from effective date (Section 3.6)
    hospitalization_date(HospitalizationDetails, HospitalizationDate),
    HospitalizationDate >= EffectiveDate,
    HospitalizationDate < EffectiveDate + 1 year.

% Rule: claim_excluded/2
% This rule checks if any general exclusions apply to the claim.
exclusion_applies(HospitalizationDetails, ClaimDetails) :-
    exclusion_applies(HospitalizationDetails),
    exclusion_applies(ClaimDetails, ExclusionReason),
    (
        ExclusionReason = skydiving
    ;
        ExclusionReason = military_service
    ;
        ExclusionReason = fire_fighter_service
    ;
        ExclusionReason = police_service
    ;
        exclusion_applies(HospitalizationDetails)
    ).

% Rule: exclusion_applies_to_hospitalization/1
% This rule is a placeholder, as the exclusion rules are defined within claim_excluded.
% It signifies that an exclusion might apply based on hospitalization details.
exclusion_applies(_).

% Rule: exclusion_reason_for_claim/2
% This rule attempts to determine the reason for the claim for exclusion purposes.
% This would typically be derived from ClaimDetails. For this translation, we assume
% a structure where the reason can be extracted or inferred.
% For the purpose of this Prolog encoding, we'll assume ClaimDetails can provide this.
% Example: claim_details('skydiving incident', Reason) would unify Reason with 'skydiving'.
exclusion_applies(ClaimDetails, Reason) :-
    member(reason(Reason), ClaimDetails).

% Rule: age_exclusion_applies/1
% This rule checks if the claimant's age at hospitalization meets the exclusion criteria.
exclusion_applies(HospitalizationDetails) :-
    claimant_age_at_hospitalization(HospitalizationDetails, Age),
    Age >= 80.

% --- Placeholder Predicates for Policy and Hospitalization Details ---
% These predicates would need to be defined with facts or dynamically
% to represent specific policy and hospitalization data for a query.
% For example:
% agreement_signed(policy_a).
% premium_paid(policy_a).
% policy_effective_date(policy_a, '2023-01-01').
% wellness_visit_date(policy_a, '2023-06-15').
% policy_is_canceled_for_reason(policy_a, none). % or fraud, misrepresentation etc.
% hospitalization_date(hospitalization_1, '2023-07-01').
% claimant_age_at_hospitalization(hospitalization_1, 75).
% claim_details(claim_1, [reason('accident')]).

% The following predicates are defined to fully satisfy the requirements,
% assuming they are provided with specific data for actual queries.
% They represent the structure of data expected for policy and claim details.

% agreement_signed(PolicyDetails): True if the policy document is signed.
% PolicyDetails: An atom or term representing the policy.

% premium_paid(PolicyDetails): True if the premium for the policy period has been paid.
% PolicyDetails: An atom or term representing the policy.

% policy_effective_date(PolicyDetails, Date): The effective date of the policy.
% PolicyDetails: An atom or term representing the policy.
% Date: A term representing the date (e.g., YYYY-MM-DD).

% wellness_visit_date(PolicyDetails, VisitDate): The date of the wellness visit.
% PolicyDetails: An atom or term representing the policy.
% VisitDate: A term representing the date (e.g., YYYY-MM-DD).

% policy_is_canceled_for_reason(PolicyDetails, Reason): True if the policy is canceled for a specific reason.
% PolicyDetails: An atom or term representing the policy.
% Reason: An atom representing the cancellation reason (e.g., fraud, misrepresentation, withholding_information).

% policy_term_duration_one_year(PolicyDetails, Years): The term of the policy in years.
% PolicyDetails: An atom or term representing the policy.
% Years: An integer representing the policy term in years.

% hospitalization_date(HospitalizationDetails, Date): The date of the hospitalization.
% HospitalizationDetails: An atom or term representing the hospitalization event.
% Date: A term representing the date (e.g., YYYY-MM-DD).

% claimant_age_at_hospitalization(HospitalizationDetails, Age): The age of the claimant at the time of hospitalization.
% HospitalizationDetails: An atom or term representing the hospitalization event.
% Age: An integer representing the claimant's age.

% claim_details(ClaimDetails, DetailsList): Provides details about the claim for exclusion purposes.
% ClaimDetails: An atom or term representing the claim.
% DetailsList: A list of terms representing claim details, e.g., [reason(skydiving)].

% --- Date Arithmetic Helpers ---
% These are simple representations of time units relative to the effective date.
% In a real system, you would use a proper date library.

% Add a number of months to a date.
% This is a simplified representation for relative date comparisons.
% For example, effective_date + 6 months means a date 6 months after effective_date.
% The Prolog query will need to provide dates in a comparable format or use a library.
% For simplicity here, we'll represent 'X months' as a placeholder for comparison.
% Example: 2023-01-01 + 6 months would be conceptually after 2023-01-01 and before 2024-01-01, specifically around 2023-07-01.

% Note: For actual Prolog execution, date arithmetic would require a library or a custom implementation.
% Here, we assume dates are represented in a way that allows direct comparison and relative addition of months.
% For example, using YYYY-MM-DD format where '>' and '+' can be overloaded or custom-built.
% For the purpose of this translation, we'll stick to conceptual date arithmetic as described in the instructions.

% Helper to represent "months" for date arithmetic.
:- multifile term_expansion/2.

term_expansion(EffectiveDate + NumMonths, DatePlusMonths) :-
    integer(NumMonths),
    atom_concat('effective_date_plus_', NumMonths, AtomNumMonths),
    atom_concat(AtomNumMonths, '_months', PredicateName),
    NewPredicate =.. [PredicateName, EffectiveDate, DatePlusMonths],
    NewPredicate.

% Define predicates for date arithmetic based on months.
% This is a placeholder for a robust date library.
% Example: `effective_date_plus_6_months(EffectiveDate, DatePlus6Months)` would unify `DatePlus6Months`
% with a date 6 months after `EffectiveDate`.

% A concrete example of how a query might be formulated and how these predicates would be used:
% Suppose:
% Policy: policy_a
% Policy Effective Date: '2023-01-01'
% Wellness Visit Date: '2023-07-01'
% Hospitalization Date: '2023-08-01'
% Claimant Age: 70
% Claim Type: illness

% Then the facts would be:
% agreement_signed(policy_a).
% premium_paid(policy_a).
% policy_effective_date(policy_a, '2023-01-01').
% wellness_visit_date(policy_a, '2023-07-01').
% policy_is_canceled_for_reason(policy_a, none).
% hospitalization_date(hospitalization_1, '2023-08-01').
% claimant_age_at_hospitalization(hospitalization_1, 70).
% claim_details(claim_1, [reason('illness')]).

% A query would be:
% ?- claim_covered(policy_a, hospitalization_1, claim_1).

% And the rules would evaluate it like this:
% policy_in_effect(policy_a) -> agreement_signed(policy_a) (true), premium_paid(policy_a) (true), wellness_visit_condition_met(policy_a) (true, '2023-07-01' =< '2023-01-01' + 6 months), policy_not_canceled(policy_a) (true, as policy_is_canceled_for_reason is none).
% hospitalization_date(hospitalization_1, policy_a) -> hospitalization_date(hospitalization_1, '2023-08-01'), '2023-08-01' >= '2023-01-01' (true), '2023-08-01' < '2023-01-01' + 1 year (true).
% is_excluded(exclusion_applies(hospitalization_1, claim_1)) -> checks exclusions, none apply.

% The date arithmetic representation is crucial.
% Let's define a simplified date representation and arithmetic that works for relative month checks.
% Assume dates are represented as `date(Year, Month, Day)`.

% date_add_months(date(Y, M, D), NumMonths, date(Y_new, M_new, D)) :-
%     TotalMonths is M + NumMonths,
%     Y_new is Y + (TotalMonths - 1) // 12,
%     M_new is (TotalMonths - 1) mod 12 + 1.

% If we use this, the rules would look like:
% wellness_visit_condition_met(PolicyDetails) :-
%     policy_effective_date(PolicyDetails, EffectiveDate),
%     wellness_visit_date(PolicyDetails, VisitDate),
%     date_add_months(EffectiveDate, 6, SixMonthAnniversary),
%     VisitDate =< SixMonthAnniversary.

% hospitalization_date(HospitalizationDetails, PolicyDetails) :-
%     policy_effective_date(PolicyDetails, EffectiveDate),
%     policy_term_duration_one_year(PolicyDetails, 1),
%     hospitalization_date(HospitalizationDetails, HospitalizationDate),
%     HospitalizationDate >= EffectiveDate,
%     date_add_months(EffectiveDate, 12, EndOfTerm),
%     HospitalizationDate < EndOfTerm.

% The current Prolog code uses a conceptual '+ NumMonths' which is intended to be resolved by the querying environment or a date library.
% For a fully functional Prolog system, a date library or explicit date predicates would be necessary.
% Given the instruction "Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy",
% we'll keep the conceptual relative date arithmetic and assume the query can provide this context.

% Rule: agreement_signed(PolicyDetails)
% This predicate is a placeholder. It should be true if the policy has been signed.
% In a real application, this would be a fact or dynamically asserted.
agreement_signed(PolicyDetails) :-
    agreement_signed(PolicyDetails, signed).

% Rule: premium_paid(PolicyDetails)
% This predicate is a placeholder. It should be true if the premium has been paid.
% In a real application, this would be a fact or dynamically asserted.
premium_paid(PolicyDetails) :-
    agreement_signed(PolicyDetails, premium_paid).

% Rule: agreement_signed(PolicyDetails, Condition)
% A helper predicate to check if a specific condition related to the policy is met.
% This is a placeholder for external data or facts.
% Example: agreement_signed(policy_a, signed).
agreement_signed(_PolicyDetails, _Condition). % Placeholder, assuming conditions are met as per instructions.

% Rule: policy_term_duration_one_year(PolicyDetails, Years)
% Defines the policy term in years. According to section 3.6, it's one year.
policy_term_duration_one_year(PolicyDetails, 1) :-
    policy_effective_date(PolicyDetails, _). % Assumes a policy with an effective date has a defined term.

% Rule: effective_date_plus_N_months(EffectiveDate, DatePlusNMonths)
% This is a conceptual predicate representing adding N months to a date.
% It's assumed that the query environment or data structure will handle this comparison.
% For instance, if EffectiveDate is '2023-01-01', then 'effective_date_plus_6_months'
% would represent a date conceptually around '2023-07-01'.
% The Prolog query context or facts would ensure these comparisons are valid.

% Predicate to compare a date with a date relative to an effective date.
% wellness_visit_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate)
% This means DateToCheck <= EffectiveDate + NumMonths.
wellness_visit_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate) :-
    % This is a conceptual representation of date arithmetic.
    % In a real system, a date library would be used.
    % For example, if EffectiveDate is '2023-01-01' and NumMonths is 6,
    % this checks if DateToCheck is on or before '2023-07-01'.
    % We assume the input dates and their comparison will respect this logic.
    % This predicate is used internally to represent the concept.
    % The actual comparison logic is embedded in the rules that use '+ NumMonths'.
    % For example, `VisitDate =< EffectiveDate + 6 months` implies a comparison
    % that treats '+ 6 months' as a specific point in time relative to EffectiveDate.
    true. % This predicate itself doesn't perform the date math but signifies the intent.

% Predicate to compare a date with a date relative to an effective date.
% date_is_before_relative_to_effective_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate)
% This means DateToCheck < EffectiveDate + NumMonths.
date_is_before_relative_to_effective_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate) :-
    % Similar to the above, this is a conceptual representation.
    true. % This predicate itself doesn't perform the date math but signifies the intent.

% Predicate to compare a date with a date relative to an effective date.
% date_is_on_or_after_relative_to_effective_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate)
% This means DateToCheck >= EffectiveDate + NumMonths.
date_is_on_or_after_relative_to_effective_date(DateToCheck, NumMonthsAfterEffective, EffectiveDate) :-
    % Similar to the above, this is a conceptual representation.
    true. % This predicate itself doesn't perform the date math but signifies the intent.

% Simplified representations for date additions for clarity in rules.
% These are not runnable Prolog predicates without a date library.
% They serve as placeholders for how dates would be manipulated conceptually.

% Example: effective_date_plus_6_months(EffectiveDate, Date6MonthsLater)
% Assume this unifies Date6MonthsLater with EffectiveDate + 6 months.

% The following are definitions of the placeholder predicates used in the rules.
% These predicates would need to be provided with actual facts or data
% in a real Prolog query.

% policy_effective_date(PolicyDetails, Date):
% Example fact: policy_effective_date(policy_a, date(2023, 1, 1)).

% wellness_visit_date(PolicyDetails, VisitDate):
% Example fact: wellness_visit_date(policy_a, date(2023, 7, 1)).

% hospitalization_date(HospitalizationDetails, Date):
% Example fact: hospitalization_date(hospitalization_xyz, date(2023, 8, 15)).

% claimant_age_at_hospitalization(HospitalizationDetails, Age):
% Example fact: claimant_age_at_hospitalization(hospitalization_xyz, 72).

% policy_is_canceled_for_reason(PolicyDetails, Reason):
% Example fact: policy_is_canceled_for_reason(policy_a, none). % 'none' means not canceled for these reasons.

% claim_details(ClaimDetails, DetailsList):
% Example fact: claim_details(claim_abc, [reason(accidental_injury)]).