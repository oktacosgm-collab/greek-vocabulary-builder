"""modules/grammar.py – conjugation/declension rendering and gender helpers"""
import streamlit as st
from .config import ARTICLE

SG_ART = {
    "masculine": {"nominative":"ο",  "genitive":"του", "accusative":"τον", "vocative":"—"},
    "feminine":  {"nominative":"η",  "genitive":"της", "accusative":"την", "vocative":"—"},
    "neuter":    {"nominative":"το", "genitive":"του", "accusative":"το",  "vocative":"—"},
}
PL_ART = {
    "masculine": {"nominative":"οι", "genitive":"των", "accusative":"τους","vocative":"—"},
    "feminine":  {"nominative":"οι", "genitive":"των", "accusative":"τις", "vocative":"—"},
    "neuter":    {"nominative":"τα", "genitive":"των", "accusative":"τα",  "vocative":"—"},
}


def get_gender_info(data: dict) -> tuple[str, str]:
    """Returns (gender, article) for nouns, empty strings for others."""
    decl = data.get("declension", {})
    if isinstance(decl, dict) and "gender" in decl:
        gender = decl["gender"]
        return gender, ARTICLE.get(gender, "")
    return "", ""


def _art(gender: str, case: str, plural: bool = False) -> str:
    d = PL_ART if plural else SG_ART
    return d.get(gender, {}).get(case, "")


def _fmt(article: str, form: str) -> str:
    if not form or form == "—":
        return "—"
    return f"{article} {form}" if article and article != "—" else form


def _make_table(rows: list, accent_color: str = "#90cdf4") -> str:
    html = "<table style='width:100%;border-collapse:collapse;margin-bottom:16px;font-size:0.95rem;'>"
    for r_i, row in enumerate(rows):
        bg = "#1e2a3a" if r_i == 0 else ("#16213e" if r_i % 2 == 0 else "#1a1a2e")
        fw = "bold" if r_i == 0 else "normal"
        html += f"<tr style='background:{bg};'>"
        for c_i, cell in enumerate(row):
            color = accent_color if r_i == 0 or c_i == 0 else "#e2e8f0"
            html += f"<td style='padding:8px 12px;border:1px solid #2d3748;color:{color};font-weight:{fw};'>{cell}</td>"
        html += "</tr>"
    return html + "</table>"


# Accent color and bullet per tense group
TENSE_STYLE = {
    "present":          ("🟢", "#68d391"),  # green
    "past_simple":      ("🟠", "#f6ad55"),  # orange
    "past_continuous":  ("🟤", "#c6a070"),  # brown
    "past_perfect":     ("🔴", "#fc8181"),  # red
    "future_simple":    ("🔵", "#63b3ed"),  # blue
    "future_continuous":("🔷", "#76e4f7"),  # cyan
    "present_perfect":  ("🟣", "#b794f4"),  # purple
    "imperative":       ("🔺", "#f687b3"),  # pink
}


def render_conjugation(word: str, data: dict):
    conj = data.get("conjugation")
    if not conj:
        st.info("No conjugation data for this word.")
        return

    voice = conj.get("voice", "")
    if voice:
        st.markdown(f"**Voice:** {voice}")
    st.markdown("")

    # Tenses grouped by category for clarity
    tense_groups = [
        ("", [
            ("present", "Present (Simple / Continuous)"),
        ]),
        ("", [
            ("past_simple",     "Past Simple (Αόριστος)"),
            ("past_continuous", "Past Continuous (Παρατατικός)"),
            ("past_perfect",    "Past Perfect (Υπερσυντέλικος)"),
        ]),
        ("", [
            ("future_simple",     "Future Simple (Perfective)"),
            ("future_continuous", "Future Continuous (Imperfective)"),
        ]),
        ("", [
            ("present_perfect", "Present Perfect (Παρακείμενος)"),
        ]),
    ]

    for group_label, tenses in tense_groups:
        group_tenses = [(key, label) for key, label in tenses if conj.get(key)]
        if not group_tenses:
            continue

        for key, label in group_tenses:
            t = conj.get(key)
            if not t:
                continue
            bullet, accent = TENSE_STYLE.get(key, ("▪️", "#90cdf4"))
            st.markdown(f"##### {bullet} {label}")
            rows = [
                ["Person", "Singular", "Plural"],
                ["1st", t.get("sg1", "—"), t.get("pl1", "—")],
                ["2nd", t.get("sg2", "—"), t.get("pl2", "—")],
                ["3rd", t.get("sg3", "—"), t.get("pl3", "—")],
            ]
            st.markdown(_make_table(rows, accent_color=accent), unsafe_allow_html=True)

    # Imperative — special layout (only sg/pl, no person rows)
    imp = conj.get("imperative")
    if imp:
        bullet, accent = TENSE_STYLE.get("imperative", ("🔺", "#f687b3"))
        st.markdown(f"#### {bullet} Imperative (Προστακτική)")
        rows = [
            ["", "Form"],
            ["Singular", imp.get("sg", "—")],
            ["Plural",   imp.get("pl", "—")],
        ]
        st.markdown(_make_table(rows, accent_color=accent), unsafe_allow_html=True)


def render_declension(word: str, data: dict):
    decl = data.get("declension")
    if not decl:
        st.info("No declension data for this word.")
        return
    cases = ["nominative", "genitive", "accusative", "vocative"]

    # ── Adjective ──────────────────────────────────────────────────────────────
    if "masculine" in decl or "feminine" in decl or "neuter" in decl:
        genders = ["masculine", "feminine", "neuter"]
        m = decl.get("masculine", {})
        f = decl.get("feminine",  {})
        n = decl.get("neuter",    {})
        has_plural = any(
            isinstance(decl.get(g), dict) and "plural" in decl.get(g, {})
            for g in genders
        )
        if has_plural:
            st.markdown("##### Singular")
            rows = [["Case", "Masculine (ο)", "Feminine (η)", "Neuter (το)"]]
            for c in cases:
                rows.append([c.capitalize(),
                    _fmt(_art("masculine",c), m.get("singular",m).get(c,"—")),
                    _fmt(_art("feminine", c), f.get("singular",f).get(c,"—")),
                    _fmt(_art("neuter",   c), n.get("singular",n).get(c,"—"))])
            st.markdown(_make_table(rows), unsafe_allow_html=True)
            st.markdown("##### Plural")
            rows = [["Case", "Masculine (οι)", "Feminine (οι)", "Neuter (τα)"]]
            for c in cases:
                rows.append([c.capitalize(),
                    _fmt(_art("masculine",c,True), m.get("plural",{}).get(c,"—")),
                    _fmt(_art("feminine", c,True), f.get("plural",{}).get(c,"—")),
                    _fmt(_art("neuter",   c,True), n.get("plural",{}).get(c,"—"))])
            st.markdown(_make_table(rows), unsafe_allow_html=True)
        else:
            st.markdown("##### Adjective forms (singular)")
            rows = [["Case", "Masculine (ο)", "Feminine (η)", "Neuter (το)"]]
            for c in cases:
                rows.append([c.capitalize(),
                    _fmt(_art("masculine",c), m.get(c,"—")),
                    _fmt(_art("feminine", c), f.get(c,"—")),
                    _fmt(_art("neuter",   c), n.get(c,"—"))])
            st.markdown(_make_table(rows), unsafe_allow_html=True)
            st.caption("Plural forms not yet in cache. Re-run enrich_words.py --update-conjugation to add them.")

    # ── Noun ───────────────────────────────────────────────────────────────────
    elif "singular" in decl or "plural" in decl:
        gender  = decl.get("gender", "")
        article = ARTICLE.get(gender, "")
        label   = f"{article} ({gender})" if gender else "—"
        if gender:
            st.markdown(f"**Gender:** {label}")
            st.markdown("")
        sg = decl.get("singular", {})
        pl = decl.get("plural",   {})
        rows = [["Case", "Singular", "Plural"]]
        for c in cases:
            rows.append([c.capitalize(),
                _fmt(SG_ART.get(gender,{}).get(c,""), sg.get(c,"—")),
                _fmt(PL_ART.get(gender,{}).get(c,""), pl.get(c,"—"))])
        st.markdown(_make_table(rows), unsafe_allow_html=True)
    else:
        st.info("Declension format not recognised.")
