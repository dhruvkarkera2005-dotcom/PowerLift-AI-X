from powerlift_ai_x.dataset.athlete_identity import (
    collision_statistics,
    find_identity_collisions,
    find_same_competition_collisions,
    make_identity_context,
)


def make_row(
    athlete_id="ATH-1",
    year=2023,
    competition="Competition A",
    division="Open",
    weight_class="74",
    equipment="CLASSIC",
    bodyweight=73.0,
):
    return {
        "athlete_id": athlete_id,
        "year": year,
        "competition": competition,
        "division": division,
        "weight_class": weight_class,
        "equipment": equipment,
        "bodyweight": bodyweight,
    }


def test_identity_context():
    row = make_row(
        athlete_id="ATH-123",
        year="2023",
        competition="Competition A",
        division="Open",
        weight_class="74",
        equipment="CLASSIC",
        bodyweight="73.5",
    )

    context = make_identity_context(row)

    assert context.athlete_id == "ATH-123"
    assert context.year == 2023
    assert context.competition == "Competition A"
    assert context.division == "Open"
    assert context.weight_class == "74"
    assert context.equipment == "CLASSIC"
    assert context.bodyweight == 73.5


def test_different_years_are_detected_as_contexts():
    rows = [
        make_row(year=2022),
        make_row(year=2023),
    ]

    collisions = find_identity_collisions(rows)

    assert len(collisions) == 1
    assert collisions[0].athlete_id == "ATH-1"
    assert len(collisions[0].contexts) == 2


def test_same_competition_different_weight_classes_is_detected():
    rows = [
        make_row(
            year=2023,
            competition="Competition A",
            weight_class="74",
            bodyweight=73.5,
        ),
        make_row(
            year=2023,
            competition="Competition A",
            weight_class="83",
            bodyweight=82.0,
        ),
    ]

    collisions = find_same_competition_collisions(
        rows
    )

    assert len(collisions) == 1
    assert collisions[0].athlete_id == "ATH-1"
    assert len(collisions[0].contexts) == 2


def test_different_athletes_are_not_grouped():
    rows = [
        make_row(athlete_id="ATH-A"),
        make_row(athlete_id="ATH-B"),
    ]

    collisions = find_identity_collisions(rows)

    assert len(collisions) == 0


def test_identical_rows_are_one_context():
    row = make_row()

    collisions = find_identity_collisions(
        [row, row.copy()]
    )

    assert len(collisions) == 0


def test_same_competition_collision_keeps_distinct_contexts():
    rows = [
        make_row(
            weight_class="74",
            bodyweight=73.5,
        ),
        make_row(
            weight_class="83",
            bodyweight=82.0,
        ),
        make_row(
            weight_class="83",
            bodyweight=82.0,
        ),
    ]

    collisions = find_same_competition_collisions(
        rows
    )

    assert len(collisions) == 1

    contexts = collisions[0].contexts

    assert len(contexts) == 2

    assert {
        context.weight_class
        for context in contexts
    } == {"74", "83"}


def test_collision_statistics():
    rows = [
        make_row(
            athlete_id="ATH-A",
            year=2022,
        ),
        make_row(
            athlete_id="ATH-A",
            year=2023,
        ),
        make_row(
            athlete_id="ATH-B",
            year=2023,
            competition="Competition B",
        ),
        make_row(
            athlete_id="ATH-B",
            year=2023,
            competition="Competition B",
            weight_class="83",
            bodyweight=82.0,
        ),
    ]

    stats = collision_statistics(rows)

    assert stats["athlete_ids"] == 2
    assert stats["candidate_collision_ids"] == 2
    assert stats[
        "same_competition_collision_groups"
    ] == 1