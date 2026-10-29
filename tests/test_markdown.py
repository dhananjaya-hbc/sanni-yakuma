from test_render import ritual

from sanni_yakuma.markdown import MARKER, comment


def test_comment_has_demons_evidence_and_fix():
    md = comment(ritual())
    assert md.startswith(MARKER)
    assert "## Sanni Yakuma · 1 of 18 demons possess this code" in md
    assert "### Bihiri Sanniya · swallowed errors (clear)" in md
    assert "[`src/app.py:4`](https://github.com/demo/app/blob/abc1234def/src/app.py#L4)" in md
    assert "~~~~diff\n--- a/src/app.py" in md
    assert "Questioned and sent away: Golu" in md


def test_comment_cannot_ping_or_close_issues():
    md = comment(
        ritual(possessions=[], blessings=[]).model_copy(
            update={"kola_sanniya": ritual().kola_sanniya.model_copy(update={"root_cause": "Ask @octocat, fixes #12"})}
        )
    )
    assert "@octocat" not in md and "#12" not in md


def test_multiline_verse_stays_quoted():
    verse = ritual().kola_sanniya.model_copy(update={"verse_sinhala": "පළමු පේළිය\nදෙවන පේළිය"})
    md = comment(ritual(kola_sanniya=verse))
    assert "> පළමු පේළිය  \n> දෙවන පේළිය  " in md
