"""Chiffres protégés : la forme vide d'un bloc ne garde aucun chiffre, et l'historique public ne montre que les
paris réglés."""
from jinja2 import DictLoader, Environment

from probalis.site import history
from probalis.site.lock import Locker, scrub


def _env(lk: Locker) -> Environment:
    env = Environment(loader=DictLoader({
        "p.html": '<p>{% call lk(m="a-b") %}<div class="bar3 big" role="img" aria-label="1 62 %">'
                  '<i class="fav" style="width: 62%"></i><i style="width: 38%"></i></div>{% endcall %}</p>'
                  '{% call lk(free=true, hide=true) %}<button class="pk-add" type="button" data-add=\'{"p":0.62}\' '
                  'aria-label="Ajouter : Victoire A">+</button>{% endcall %}'
                  '{% call lk(own=true) %}{% if lk.pub %}<b class="lkd">00 %</b>{% else %}<b>62 %</b>{% endif %}{% endcall %}'
                  '{% call lk(on=false) %}<b>réglé 71 %</b>{% endcall %}',
    }), autoescape=True)
    env.globals["lk"] = lk
    return env


def test_public_page_has_no_numbers():
    lk = Locker()
    lk.start("fr/index")
    html = _env(lk).get_template("p.html").render()
    public = html.replace("00 %", "").replace("réglé 71 %", "")
    assert "62" not in public and "38" not in public
    assert "data-add" not in html and "style=" not in html and "fav" not in html and "aria-label" not in html
    assert "lkd" in html and "lkh" in html
    assert "réglé 71 %" in html          # bloc sans protection (on=false) : écrit tel quel


def test_real_blocks_are_sorted_by_access():
    lk = Locker()
    lk.start("fr/index")
    _env(lk).get_template("p.html").render()
    blocks = lk.all_of("fr/index")
    assert len(blocks) == 3 and "62%" in blocks["1"] and "data-add" in blocks["2"] and "62 %" in blocks["3"]
    assert lk.by_match() == {"a-b": {"fr/index": {"1": blocks["1"]}}}
    assert lk.free_of() == {"fr/index": {"2": blocks["2"]}}


def test_scrub_keeps_structure_only():
    out = scrub('<div class="scores"><div class="score best"><b>1-0</b><span>14 %</span></div></div>')
    assert out == ('<div class="scores lkd" aria-hidden="true"><div class="score"><b>—</b><span>—</span></div></div>')


def test_history_public_copy_hides_pending_bets():
    hist = {"version": 1, "days": {"2026-11-20": {"frozen": True, "built": "x",
            "tiers": {"safe": [{"id": "1|dc||1X", "mid": "1", "p": 0.8, "res": "won"},
                               {"id": "2|ou|2.5|over", "mid": "2", "p": 0.7, "res": None}]},
            "coupons": [{"p": 0.3, "res": None, "legs": [{"mid": "2"}]}],
            "matches": {"1": {"slug": "a"}, "2": {"slug": "b"}}}}}
    pub = history.public_copy(hist)
    day = pub["days"]["2026-11-20"]
    assert [c["id"] for c in day["tiers"]["safe"]] == ["1|dc||1X"]
    assert day["coupons"] == [] and list(day["matches"]) == ["1"] and day["sealed"] == 2
    # La version complète gardée sur l'ordinateur passe avant la version publique
    assert history.merge(pub, hist)["days"]["2026-11-20"] is hist["days"]["2026-11-20"]
    assert history.merge(hist, pub)["days"]["2026-11-20"] is hist["days"]["2026-11-20"]
