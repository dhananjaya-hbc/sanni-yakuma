import xml.etree.ElementTree as ET

from sanni_yakuma.demons import DEMONS
from sanni_yakuma.diagnosis import Blessing, Exorcism, KolaVerdict, Possession, Ritual
from sanni_yakuma.masks import kola_svg, mask_svg
from sanni_yakuma.omen import Evidence, Omen
from sanni_yakuma.render import render, ticks, write_gallery


def test_every_demon_has_a_valid_mask():
    for demon in DEMONS:
        root = ET.fromstring(mask_svg(demon.name))
        assert root.tag.endswith("svg") and demon.name in root.attrib["aria-label"]
    assert ET.fromstring(kola_svg()).tag.endswith("svg")


def test_ticks_escapes_before_marking_code():
    assert str(ticks("use `x<y` <b>now</b>")) == "use <code>x&lt;y</code> &lt;b&gt;now&lt;/b&gt;"


def ritual(**overrides) -> Ritual:
    omens = [
        Omen(demon="Bihiri", sickness="swallowed errors", found=True, severity_hint=2, summary="1 swallowed",
             evidence=[Evidence(path="src/app.py", line=4, snippet="except:", note="bare except")]),
        Omen(demon="Golu", sickness="silent repo", found=True, severity_hint=2, summary="README has 3 words."),
        Omen(demon="Naga", sickness="security nightmares", found=False, severity_hint=0, summary="No secrets found."),
    ]
    data = dict(
        repo="demo/app", url="https://github.com/demo/app", commit="abc1234def", model="gemma-test",
        performed_at="2026-10-29T10:00:00+00:00", omens=omens,
        blessings=[Blessing(title="Small and clear", detail="Only `app.py`.")],
        possessions=[Possession(
            demon="Bihiri", severity=2, evidence_ids=["E1"],
            monologue="I swallowed it <script>alert(1)</script> in `app.py`.",
            exorcism=Exorcism(summary="Catch it by name.", steps=["Edit `app.py`."],
                              diff="--- a/src/app.py\n+++ b/src/app.py\n@@ -4,1 +4,1 @@\n-except:\n+except OSError:\n"),
        )],
        spared=["Golu"],
        kola_sanniya=KolaVerdict(root_cause="Haste", explanation="Built in a hurry.", verse_sinhala="සුබ වේවා",
                                 verse_transliteration="suba vēvā", verse_english="May it be well"),
    )
    data.update(overrides)
    return Ritual(**data)


def test_page_shows_the_whole_ritual():
    page = render(ritual())
    assert "Bihiri Sanniya" in page and "brings deafness" in page
    assert "<code>app.py</code>" in page
    assert "https://github.com/demo/app/blob/abc1234def/src/app.py#L4" in page
    assert '<span class="del">-except:</span>' in page and '<span class="add">+except OSError:</span>' in page
    assert "Golu" in page and 'id="spared"' in page
    assert 'lang="si">සුබ වේවා' in page
    assert page.count("<svg") >= 3 + 3  # Bihiri, Golu, Kola masks plus flames and lamps


def test_gemma_text_cannot_inject_html():
    page = render(ritual())
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_page_without_demons():
    page = render(ritual(possessions=[], spared=[]))
    assert "No demon could be proven" in page and 'id="spared"' not in page


def test_gallery_links_every_ritual(tmp_path):
    rituals = [ritual(), ritual(repo="demo/well", url="https://github.com/demo/well", possessions=[], spared=[])]
    index = write_gallery(rituals, tmp_path)
    html = index.read_text()
    assert 'href="demo-app.html"' in html and 'href="demo-well.html"' in html
    assert (tmp_path / "demo-app.html").exists() and (tmp_path / ".nojekyll").exists()
    assert html.index("demo/app") < html.index("demo/well")  # most possessed first
