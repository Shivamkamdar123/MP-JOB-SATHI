# Eligibility Decisions

`likely` means: all hard constraints pass but a soft check is unknown or low-confidence.

Hard constraints include age at the notification's as-on date, applicable age-relaxation rules, qualification, required certificates, post-level gender/PwD/ex-serviceman restrictions, domicile, and employment-exchange requirements. Missing hard-constraint data produces `needs_check`; it never produces `likely` or `eligible`.

Qualification rules within one post are any-of alternatives. One matching alternative is sufficient for the qualification constraint; failures in other alternatives do not downgrade that post. If none matches and at least one is unknown, the result is `needs_check`; if all fail, the post is `not_eligible`.

The current soft check is role relevance when the post-title provenance confidence is below 0.70. It cannot override a failed or unknown hard constraint. The `manual_likely_one_alternative_matches` case is therefore `eligible`: its Civil qualification alternative passes, and an Electrical alternative failing is irrelevant under any-of semantics. The `manual_likely_low_confidence_title_*` cases are `likely`: their hard constraints pass and only the low-confidence role-relevance check remains unresolved.