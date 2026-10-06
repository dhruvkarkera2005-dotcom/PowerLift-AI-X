from powerlift_ai_x.identity.resolver import (
    IdentityCandidate,
    IdentityDecision,
    resolve_identity_pair,
)


def make_candidate(
    *,
    dob=None,
    team=None,
    lot=None,
    bodyweight=74.0,
    division="Open",
    weight_class="74",
    equipment="CLASSIC",
):
    return IdentityCandidate(
        athlete_id="ATH-test",
        date_of_birth=dob,
        team=team,
        lot=lot,
        bodyweight=bodyweight,
        division=division,
        weight_class=weight_class,
        equipment=equipment,
    )


def test_same_dob_is_same_athlete():
    left = make_candidate(
        dob="22-09-1996",
        team="PUN",
    )

    right = make_candidate(
        dob="22-09-1996",
        team="UP",
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.SAME
    assert result.reason == "SAME_DATE_OF_BIRTH"


def test_different_dob_is_split():
    left = make_candidate(
        dob="14-05-1992",
    )

    right = make_candidate(
        dob="30-10-1990",
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.SPLIT
    assert result.reason == "DIFFERENT_DATE_OF_BIRTH"


def test_missing_dob_is_unresolved():
    left = make_candidate(
        dob=None,
    )

    right = make_candidate(
        dob=None,
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.UNRESOLVED
    assert result.reason == "INSUFFICIENT_IDENTITY_METADATA"


def test_same_dob_different_division_is_same():
    left = make_candidate(
        dob="19-02-2000",
        division="Junior",
        weight_class="66",
        bodyweight=65.2,
    )

    right = make_candidate(
        dob="19-02-2000",
        division="Open",
        weight_class="66",
        bodyweight=65.7,
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.SAME


def test_same_dob_different_weight_class_is_same():
    left = make_candidate(
        dob="30-03-1998",
        weight_class="59",
        bodyweight=59.0,
    )

    right = make_candidate(
        dob="30-03-1998",
        weight_class="74",
        bodyweight=73.4,
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.SAME


def test_missing_dob_does_not_guess_from_team():
    left = make_candidate(
        dob=None,
        team="KER",
        bodyweight=82.4,
    )

    right = make_candidate(
        dob=None,
        team="KER",
        bodyweight=83.0,
    )

    result = resolve_identity_pair(
        left,
        right,
    )

    assert result.decision == IdentityDecision.UNRESOLVED