"""app.py — Greek Flashcard App (main entry point)"""

import streamlit as st
import random
import html as _html
from datetime import date

from modules.config      import ARTICLE, AUDIO_DIR
from modules.data_loader import load_cache, load_raw_words, build_word_map
from modules.audio       import play_sequence
from modules.word_export import build_word_doc
from modules.grammar     import get_gender_info, render_conjugation, render_declension
from modules.i18n        import t, render_language_selector
from modules import srs as SRS

def loc(data: dict, field: str, fallback: str = "--") -> str:
    """Return language-aware field, falling back to English."""
    from modules.i18n import get_lang_code
    lang = get_lang_code()
    if lang != "en":
        val = data.get(f"{field}_{lang}")
        if val:
            return val
    return data.get(field, fallback)

st.set_page_config(page_title="Greek Flashcards", page_icon="🇬🇷",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS ────────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 24px; padding: 40px; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08);
    min-height: 340px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; margin: 12px 0;
}
.card-back { background: linear-gradient(135deg, #0a2a0a 0%, #1a3a1a 50%, #0d4d0d 100%); }
.card-srs  { background: linear-gradient(135deg, #1a0a2e 0%, #2a1060 50%, #1a0a3e 100%); }
.greek-word { font-size: 3.2rem; font-weight: 700; color: #e8d5b7; letter-spacing: 2px; margin-bottom: 8px; }
.transliteration { font-size: 1.15rem; color: #a0aec0; font-style: italic; margin-bottom: 12px; }
.pos-badge {
    display: inline-block; background: rgba(100,149,237,0.25); color: #90cdf4;
    border: 1px solid rgba(100,149,237,0.4); border-radius: 20px;
    padding: 4px 16px; font-size: 0.8rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
}
.diff-badge {
    display: inline-block; background: rgba(246,173,85,0.2); color: #f6ad55;
    border: 1px solid rgba(246,173,85,0.35); border-radius: 20px;
    padding: 4px 14px; font-size: 0.78rem; font-weight: 600; margin-left: 8px;
}
.srs-badge {
    display: inline-block; background: rgba(167,139,250,0.2); color: #c4b5fd;
    border: 1px solid rgba(167,139,250,0.35); border-radius: 20px;
    padding: 4px 14px; font-size: 0.78rem; font-weight: 600; margin-left: 8px;
}
.translation { font-size: 1.6rem; font-weight: 600; color: #68d391; margin-bottom: 10px; }
.definition { font-size: 1.05rem; color: #cbd5e0; margin-bottom: 16px; max-width: 600px; line-height: 1.6; }
.example-greek { font-size: 1.25rem; color: #fbd38d; font-style: italic; margin-bottom: 6px; font-weight: 500; }
.example-en { font-size: 0.95rem; color: #718096; }
.example-divider { border: none; border-top: 1px solid rgba(255,255,255,0.1); width: 70%; margin: 16px auto; }
.flip-hint { font-size: 0.75rem; color: rgba(255,255,255,0.2); margin-top: 24px; }
.gender-badge {
    display: inline-block; background: rgba(236,72,153,0.2); color: #f9a8d4;
    border: 1px solid rgba(236,72,153,0.35); border-radius: 20px;
    padding: 4px 14px; font-size: 0.78rem; font-weight: 600; margin-left: 8px;
}
.progress-text { font-size: 0.85rem; color: #718096; text-align: center; margin-bottom: 6px; }
.stat-box { background: #1e2a3a; border-radius: 12px; padding: 12px 16px; text-align: center; border: 1px solid #2d3748; }
.stat-num  { font-size: 1.8rem; font-weight: 700; }
.stat-label{ font-size: 0.75rem; color: #a0aec0; }
section[data-testid="stSidebar"] { background: #0d1117 !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] input[type="text"] {
    background-color: #1e2a3a !important; color: #e2e8f0 !important;
    border: 1px solid #4a5568 !important; border-radius: 6px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] { background-color: #1e2a3a !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] * { background-color: #1e2a3a !important; color: #e2e8f0 !important; }
section[data-testid="stSidebar"] [data-baseweb="popover"] *,
section[data-testid="stSidebar"] [data-baseweb="menu"] * { background-color: #1e2a3a !important; color: #e2e8f0 !important; }
section[data-testid="stSidebar"] button { background-color: #2d3748 !important; color: #e2e8f0 !important; border: 1px solid #4a5568 !important; }
section[data-testid="stSidebar"] button p { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] button:hover { background-color: #4a5568 !important; }
section[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #68d391 !important; font-size: 1.6rem !important; }
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #a0aec0 !important; }
section[data-testid="stSidebar"] .stProgress > div > div { background: #3182ce !important; }
section[data-testid="stSidebar"] hr { border-color: #2d3748 !important; }
section[data-testid="stSidebar"] .stCheckbox span { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stRadio label { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] { background-color: #3182ce !important; }
section[data-testid="stSidebar"] .stMultiSelect * { color: #e2e8f0 !important; background-color: #1e2a3a !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Load data ───────────────────────────────────────────────────────────────────────────────
cache     = load_cache()
raw_words = load_raw_words()
all_words = build_word_map(cache, raw_words)
word_list = list(all_words.keys())
srs_data  = SRS.load_srs()

# ── Session state ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "card_index": 0, "flipped": False, "shuffled": [], "filter_diffs": [],
    "score": {"known":0,"review":0},
    "quiz_index": 0, "quiz_score": {"correct":0,"wrong":0},
    "quiz_words": [], "quiz_failed": [], "quiz_answer": None, "quiz_done": False,
    "quiz_mode": "multiple_choice",
    "lt_words": [], "lt_index": 0, "lt_score": {"correct":0,"wrong":0},
    "lt_failed": [], "lt_done": False, "lt_submitted": False, "lt_target": "word",
    "srs_queue": [], "srs_index": 0, "srs_revealed": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_language_selector()
    st.markdown("---")
    st.markdown(f"## {t('sidebar_title')}")
    enriched = sum(1 for w in word_list if w in cache)
    st.markdown(t("words_enriched", enriched=enriched, total=len(word_list)))
    st.progress(enriched / max(len(word_list), 1))
    stats = SRS.get_stats(srs_data, [w for w in word_list if w in cache])
    st.markdown(t("srs_stats", due=stats['due'], new=stats['new'], mature=stats['mature']))
    st.markdown("---")

    st.markdown(f"### {t('filters')}")
    diff_levels = ["A1","A2","B1","B2","C1","C2"]
    sel_diffs = st.multiselect(t("difficulty"), diff_levels, placeholder=t("all_levels"), label_visibility="collapsed")
    prev = st.session_state.get("filter_diffs", [])
    if sel_diffs != prev:
        st.session_state["filter_diffs"] = sel_diffs
        st.session_state.card_index = 0
        st.session_state.flipped    = False
        st.session_state.shuffled   = []
    sel_diff = ", ".join(sel_diffs) if sel_diffs else "All"
    shuffle = st.checkbox(t("shuffle_cards"), value=True)
    filtered = [w for w in word_list if not sel_diffs or all_words[w].get("difficulty","") in sel_diffs]
    if not st.session_state.shuffled or len(st.session_state.shuffled) != len(filtered):
        idx = list(range(len(filtered)))
        if shuffle: random.shuffle(idx)
        st.session_state.shuffled = idx
    st.markdown("---")

    st.markdown(f"### {t('search')}")
    import locale, unicodedata
    try:
        locale.setlocale(locale.LC_COLLATE, "el_GR.UTF-8")
        sorted_words = sorted(word_list, key=locale.strxfrm)
    except locale.Error:
        def _greek_key(w):
            return unicodedata.normalize("NFD", w.lower()).encode("ascii","ignore").decode()
        sorted_words = sorted(word_list, key=_greek_key)
    greek_options = [t("select_word")] + sorted_words
    chosen = st.selectbox("Search", greek_options, label_visibility="collapsed", key="sidebar_search_input")
    matches = []
    if chosen != t("select_word"):
        matches = [chosen]
        if st.session_state.get("chosen_word") != chosen:
            st.session_state["chosen_word"] = chosen
        if st.button(t("go"), use_container_width=True):
            target = st.session_state["chosen_word"]
            if target in filtered:
                target_pos = filtered.index(target)
                for pos, idx in enumerate(st.session_state.shuffled):
                    if idx == target_pos:
                        st.session_state.card_index = pos
                        st.session_state.flipped    = False
                        st.rerun()
            else:
                st.warning(t("not_in_filter"))
    st.markdown("---")

    c1, c2 = st.columns(2)
    c1.metric(t("known"), st.session_state.score["known"])
    c2.metric(t("review"), st.session_state.score["review"])
    if st.button(t("reset_session")):
        st.session_state.update(card_index=0, flipped=False, score={"known":0,"review":0})
        idx = list(range(len(filtered)))
        if shuffle: random.shuffle(idx)
        st.session_state.shuffled = idx
        st.rerun()
    st.markdown("---")

    st.markdown(t("export_to_word"))
    _scope_all = t("export_scope_all"); _scope_filter = t("export_scope_filter"); _scope_search = t("export_scope_search")
    export_scope = st.radio("Export", [_scope_all, _scope_filter, _scope_search], label_visibility="collapsed")
    if export_scope == _scope_all: export_words = word_list
    elif export_scope == _scope_filter: export_words = filtered
    else: export_words = matches if matches else word_list
    st.markdown(t("words_will_export", count=len(export_words)))
    st.markdown(t("include_fields"))
    exp_pos         = st.checkbox(t("field_pos"), value=True)
    exp_translation = st.checkbox(t("field_translation"), value=True)
    exp_definition  = st.checkbox(t("field_definition"), value=False)
    exp_example     = st.checkbox(t("field_example"), value=True)
    export_opts = {"pos":exp_pos,"translation":exp_translation,"definition":exp_definition,"example":exp_example}
    if st.button(t("generate_word_file"), use_container_width=True, type="primary"):
        with st.spinner(t("building_word_doc", count=len(export_words))):
            buf = build_word_doc(export_words, all_words, export_opts)
        st.download_button(label=t("download_docx"), data=buf,
            file_name="greek_vocabulary.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True)

# ── Tabs ────────────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("tab_flashcard"), t("tab_srs"), t("tab_browse"),
    t("tab_conjugation"), t("tab_test")
])

# ────────────────────────────────────────────────────────────────────────────────
# TAB 1 — FLASHCARD
# ────────────────────────────────────────────────────────────────────────────────
with tab1:
    if not filtered:
        st.info(t("no_words_filter"))
        st.stop()
    total   = len(filtered)
    pos_raw = st.session_state.card_index % total
    word    = filtered[st.session_state.shuffled[pos_raw]]
    data    = all_words[word]
    ex      = data.get("example_greek","")
    ex_en   = loc(data, "example_english", "")
    st.markdown(f"<p class='progress-text'>{t('card_progress', current=pos_raw+1, total=total, filter=sel_diff)}</p>", unsafe_allow_html=True)
    st.progress((pos_raw+1)/total)
    gender, article = get_gender_info(data)
    gender_html = f'<span class="gender-badge">{article} ({gender})</span>' if gender else ""
    w_safe=_html.escape(word); pos_safe=_html.escape(data.get("part_of_speech","--"))
    dif_safe=_html.escape(data.get("difficulty","?")); tra_safe=_html.escape(data.get("transliteration","--"))
    tr_safe=_html.escape(loc(data, "translation")); df_safe=_html.escape(loc(data, "definition"))
    ex_safe=_html.escape(ex) if ex else "--"; exen_safe=_html.escape(ex_en) if ex_en else ""
    if not st.session_state.flipped:
        card_html = ('<div class="card">'+f'<span class="pos-badge">{pos_safe}</span>'+f'<span class="diff-badge">{dif_safe}</span>'+f'{gender_html}'+f'<div class="greek-word">{w_safe}</div>'+f'<div class="transliteration">[ {tra_safe} ]</div>'+'<hr class="example-divider">'+f'<div class="example-greek"><span style="font-size:0.8rem;opacity:0.6;">Παράδειγμα</span><br>{ex_safe}</div>'+f'<div class="flip-hint">{t("flip_hint")}</div>'+'</div>')
    else:
        card_html = ('<div class="card card-back">'+f'<div class="greek-word" style="font-size:2rem;">{w_safe}</div>'+f'{gender_html}'+f'<div class="translation">{tr_safe}</div>'+f'<div class="definition">{df_safe}</div>'+'<hr class="example-divider">'+f'<div class="example-greek"><span style="font-size:0.8rem;opacity:0.6;">Παράδειγμα</span><br>{ex_safe}</div>'+f'<div class="example-en" style="display:block;margin-top:6px;">{exen_safe}</div>'+'</div>')
    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    b1,b2,b3,b4,b5 = st.columns([1.2,1.5,1.6,1.2,1.2])
    with b1:
        if st.button(t("btn_prev"), use_container_width=True):
            st.session_state.card_index=max(0,st.session_state.card_index-1); st.session_state.flipped=False; st.rerun()
    with b2:
         if st.button(t("btn_read_aloud"), use_container_width=True, type="primary"): play_sequence(data,word)
    with b3:
        lbl=t("btn_flip") if not st.session_state.flipped else t("btn_reset_card")
        if st.button(lbl, use_container_width=True): st.session_state.flipped=not st.session_state.flipped; st.rerun()
    with b4:
        if st.session_state.flipped and st.button(t("btn_known"), use_container_width=True):
            st.session_state.score["known"]+=1; st.session_state.card_index+=1; st.session_state.flipped=False; st.rerun()
    with b5:
        if st.button(t("btn_next"), use_container_width=True):
            st.session_state.card_index+=1; st.session_state.flipped=False; st.rerun()
    if st.session_state.flipped:
        st.markdown("<br>", unsafe_allow_html=True)
        _,mid,_ = st.columns([2,1,2])
        with mid:
            if st.button(t("btn_mark_review"), use_container_width=True):
                st.session_state.score["review"]+=1; st.session_state.card_index+=1; st.session_state.flipped=False; st.rerun()

# ────────────────────────────────────────────────────────────────────────────────
# TAB 2 — SPACED REPETITION
# ────────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(t("srs_title"))
    enriched_words = [w for w in filtered if w in cache]
    stats = SRS.get_stats(srs_data, enriched_words)
    s1,s2,s3,s4 = st.columns(4)
    s1.markdown(f"<div class='stat-box'><div class='stat-num' style='color:#f6ad55;'>{stats['due']}</div><div class='stat-label'>{t('srs_due')}</div></div>", unsafe_allow_html=True)
    s2.markdown(f"<div class='stat-box'><div class='stat-num' style='color:#90cdf4;'>{stats['new']}</div><div class='stat-label'>{t('srs_new')}</div></div>", unsafe_allow_html=True)
    s3.markdown(f"<div class='stat-box'><div class='stat-num' style='color:#fbd38d;'>{stats['learning']}</div><div class='stat-label'>{t('srs_learning')}</div></div>", unsafe_allow_html=True)
    s4.markdown(f"<div class='stat-box'><div class='stat-num' style='color:#68d391;'>{stats['mature']}</div><div class='stat-label'>{t('srs_mature')}</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    due_words = SRS.get_due_words(srs_data, enriched_words)
    new_words = SRS.get_new_words(srs_data, enriched_words)
    col_due,col_new,col_all = st.columns(3)
    with col_due:
        if st.button(t("btn_review_due", n=len(due_words)), use_container_width=True, type="primary", disabled=len(due_words)==0):
            st.session_state.srs_queue=due_words.copy(); st.session_state.srs_index=0; st.session_state.srs_revealed=False; st.rerun()
    with col_new:
        if st.button(t("btn_review_new", n=min(20,len(new_words))), use_container_width=True, disabled=len(new_words)==0):
            batch=new_words[:20]; random.shuffle(batch)
            st.session_state.srs_queue=batch; st.session_state.srs_index=0; st.session_state.srs_revealed=False; st.rerun()
    with col_all:
        if st.button(t("btn_review_all"), use_container_width=True, disabled=len(due_words)+len(new_words)==0):
            combined=due_words+new_words[:20]; random.shuffle(combined)
            st.session_state.srs_queue=combined; st.session_state.srs_index=0; st.session_state.srs_revealed=False; st.rerun()
    st.markdown("---")
    queue=st.session_state.srs_queue; si=st.session_state.srs_index
    if not queue:
        if stats["due"]==0 and stats["new"]==0: st.success(t("srs_nothing_due"))
        else: st.info(t("srs_choose_mode"))
    elif si>=len(queue):
        st.success(t("srs_session_complete", n=len(queue)))
        if st.button(t("btn_start_another")):
            st.session_state.srs_queue=[]; st.session_state.srs_index=0; st.rerun()
    else:
        srs_word=queue[si]; srs_data_w=all_words[srs_word]
        card=SRS.get_card(srs_data,srs_word); revealed=st.session_state.srs_revealed
        st.markdown(f"<p class='progress-text'>{t('card_progress', current=si+1, total=len(queue), filter='')}</p>", unsafe_allow_html=True)
        st.progress(si/len(queue))
        reps=card.get("repetitions",0)
        if srs_word not in srs_data: srs_label=t("srs_new_label")
        elif reps<3: srs_label=t("srs_learning_label", n=reps)
        else: srs_label=t("srs_mature_label", n=reps)
        sw_safe=_html.escape(srs_word); str_safe=_html.escape(srs_data_w.get("transliteration","--"))
        str_pos=_html.escape(srs_data_w.get("part_of_speech","--")); str_dif=_html.escape(srs_data_w.get("difficulty","?"))
        srs_ex=_html.escape(srs_data_w.get("example_greek","")); srs_exen=_html.escape(loc(srs_data_w, "example_english", ""))
        srs_tr=_html.escape(loc(srs_data_w, "translation")); srs_df=_html.escape(loc(srs_data_w, "definition"))
        sg,sa=get_gender_info(srs_data_w); sgender_html=f'<span class="gender-badge">{sa} ({sg})</span>' if sg else ""
        if not revealed:
            ch=('<div class="card card-srs">'+f'<span class="pos-badge">{str_pos}</span>'+f'<span class="diff-badge">{str_dif}</span>'+f'<span class="srs-badge">{srs_label}</span>'+f'<div class="greek-word">{sw_safe}</div>'+f'<div class="transliteration">[ {str_safe} ]</div>'+(f'<hr class="example-divider"><div class="example-greek"><span style="font-size:0.8rem;opacity:0.6;">{t("example_label")}</span><br>{srs_ex}</div>' if srs_ex else '')+f'<div class="flip-hint">{t("srs_reveal_hint")}</div></div>')
            st.markdown(ch, unsafe_allow_html=True); st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("btn_reveal"), use_container_width=True, type="primary"):
                st.session_state.srs_revealed=True; st.rerun()
        else:
            ch=('<div class="card card-srs">'+f'<span class="pos-badge">{str_pos}</span>'+f'<span class="diff-badge">{str_dif}</span>'+f'<span class="srs-badge">{srs_label}</span>'+f'{sgender_html}'+f'<div class="greek-word">{sw_safe}</div>'+f'<div class="transliteration">[ {str_safe} ]</div>'+f'<div class="translation">{srs_tr}</div>'+f'<div class="definition">{srs_df}</div>'+(f'<hr class="example-divider"><div class="example-greek"><span style="font-size:0.8rem;opacity:0.6;">{t("example_label")}</span><br>{srs_ex}</div><div class="example-en" style="display:block;margin-top:6px;">{srs_exen}</div>' if srs_ex else '')+'</div>')
            st.markdown(ch, unsafe_allow_html=True); st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(t("srs_rate"))
            q_cols=st.columns(4)
            for ci,(q,label,tooltip) in enumerate(SRS.QUALITY_BUTTONS):
                with q_cols[ci]:
                    if st.button(label, key=f"srs_q_{si}_{q}", use_container_width=True, help=tooltip):
                        updated=SRS.review(SRS.get_card(srs_data,srs_word),q)
                        srs_data[srs_word]=updated; SRS.save_srs(srs_data)
                        st.session_state.srs_index+=1; st.session_state.srs_revealed=False; st.rerun()
        _,skip_col=st.columns([4,1])
        with skip_col:
            if st.button(t("btn_skip"), use_container_width=True):
                st.session_state.srs_index+=1; st.session_state.srs_revealed=False; st.rerun()

# ────────────────────────────────────────────────────────────────────────────────
# TAB 3 — BROWSE
# ────────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(t("browse_title"))
    search=st.text_input(t("search"), placeholder=t("browse_search_placeholder"))
    only_enriched=st.checkbox(t("only_enriched"))
    display=[w for w in word_list if (not search or search.lower() in w.lower() or search.lower() in all_words[w].get("translation","").lower() or search.lower() in all_words[w].get("definition","").lower()) and (not only_enriched or w in cache)]
    st.markdown(t("n_words", n=len(display)))
    for i,w in enumerate(display[:200]):
        d=all_words[w]
        with st.expander(f"**{w}** — {loc(d, 'translation')}  {'✅' if w in cache else '⬜'}"):
            c1,c2=st.columns([3,1])
            with c1:
                if w in cache:
                    card=SRS.get_card(srs_data,w); due_str=card.get("due","--")
                    st.markdown(f"*{d.get('transliteration','--')}* · {d.get('part_of_speech','--')} · {d.get('difficulty','?')} · {t('next_review', date=due_str)}")
                    st.markdown(f"{t('label_definition')} {loc(d, 'definition')}"); st.markdown(f"{t('label_example_gr')} *{d.get('example_greek','--')}*"); st.markdown(f"{t('label_example_en')} {loc(d, 'example_english')}")
                else: st.info(t("not_yet_enriched"))
            with c2:
                if st.button("🔊", key=f"b_{i}"): play_sequence(d,w)
    if len(display)>200: st.info(t("showing_200", n=len(display)))

# ────────────────────────────────────────────────────────────────────────────────
# TAB 4 — CONJUGATION & DECLENSION
# ────────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(t("conj_title"))
    has_data=[w for w in word_list if w in cache and (cache[w].get("conjugation") or cache[w].get("declension"))]
    verbs=[w for w in has_data if cache[w].get("conjugation")]; nouns_adj=[w for w in has_data if cache[w].get("declension")]
    st.markdown(t("conj_stats", verbs=len(verbs), nouns=len(nouns_adj))); st.markdown("---")
    col_s,col_p=st.columns([3,1])
    _type_all=t("type_all"); _type_verbs=t("type_verbs"); _type_nouns=t("type_nouns")
    with col_s: t3_search=st.text_input(t("search_word"), placeholder=t("browse_search_placeholder"), key="t3_search")
    with col_p: t3_pos=st.selectbox(t("type_all"),[ _type_all, _type_verbs, _type_nouns],key="t3_pos")
    pool=verbs if t3_pos==_type_verbs else nouns_adj if t3_pos==_type_nouns else has_data
    if t3_search:
        sq=t3_search.lower(); pool=[w for w in pool if sq in w.lower() or sq in cache[w].get("translation","").lower() or sq in cache[w].get("transliteration","").lower()]
    st.markdown(t("n_words", n=len(pool)))
    for w in pool[:100]:
        d=cache[w]
        with st.expander(f"**{w}** — {loc(d, 'translation')}  ·  *{d.get('part_of_speech','')}*"):
            st.markdown(f"*[ {d.get('transliteration','--')} ]*  ·  {d.get('difficulty','?')}"); st.markdown(f"{loc(d, 'definition', '')}"); st.markdown("")
            if d.get("conjugation"): st.markdown(t("conjugation")); render_conjugation(w,d)
            if d.get("declension"): st.markdown(t("declension")); render_declension(w,d)
    if len(pool)>100: st.info(t("showing_100", n=len(pool)))

# ────────────────────────────────────────────────────────────────────────────────
# TAB 5 — TEST KNOWLEDGE
# ────────────────────────────────────────────────────────────────────────────────
with tab5:
    import unicodedata as _ud

    def _norm(s):
        """Lowercase, strip accents, strip punctuation for fuzzy compare."""
        s = s.lower().strip()
        s = _ud.normalize("NFD", s)
        s = "".join(c for c in s if _ud.category(c) != "Mn")
        s = "".join(c for c in s if c.isalpha() or c.isspace())
        return s.strip()

    def _edit_distance(a, b):
        """Simple Levenshtein distance."""
        if a == b: return 0
        if not a: return len(b)
        if not b: return len(a)
        prev = list(range(len(b)+1))
        for i, ca in enumerate(a, 1):
            curr = [i]
            for j, cb in enumerate(b, 1):
                curr.append(min(prev[j]+1, curr[j-1]+1, prev[j-1]+(ca!=cb)))
            prev = curr
        return prev[-1]

    def _score_answer(user_input, correct):
        """
        Returns (result, message)
        result: 'correct' | 'close' | 'wrong'
        """
        u = _norm(user_input)
        c = _norm(correct)
        if u == c:
            return "correct", "Exact match"
        dist = _edit_distance(u, c)
        threshold = 1 if len(c) <= 5 else 2
        if dist <= threshold:
            return "close", f"Close enough (minor typo)"
        return "wrong", f"Incorrect"

    def _ensure_audio(word, data):
        """Return audio paths — generate locally if available, otherwise R2 is used."""
        from modules.audio import safe_fn
        safe = safe_fn(word)
        w_p = AUDIO_DIR / f"{safe}_word.mp3"
        e_p = AUDIO_DIR / f"{safe}_example.mp3"
        try:
            from modules.audio import gen_gtts
            ex = data.get("example_greek", "")
            if not w_p.exists(): gen_gtts(word, "el", w_p)
            if ex and not e_p.exists(): gen_gtts(ex, "el", e_p)
        except ImportError:
            pass  # Cloud environment — audio served from R2
        return w_p, e_p

    st.markdown(t("test_title"))

    # ── Mode toggle ───────────────────────────────────────────────────────────
    mode = st.radio("Mode", [t("mode_multiple"), t("mode_listen")],
                    horizontal=True, label_visibility="collapsed",
                    key="quiz_mode_radio")
    quiz_mode = "listen_type" if mode == t("mode_listen") else "multiple_choice"
    if st.session_state.get("quiz_mode") != quiz_mode:
        st.session_state["quiz_mode"] = quiz_mode

    st.markdown("---")

    # ── Level filter (independent of sidebar) ────────────────────────────────
    all_levels = ["A1","A2","B1","B2","C1","C2"]
    sel_levels = st.multiselect(t("difficulty_levels"), all_levels, default=[],
                                key="quiz_levels", label_visibility="visible")
    quiz_pool = [w for w in filtered if w in cache and cache[w].get("translation")
                 and (not sel_levels or cache[w].get("difficulty","") in sel_levels)]
    level_str = ", ".join(sel_levels) if sel_levels else "all"
    st.caption(t("words_available", n=len(quiz_pool), levels=level_str))
    if len(quiz_pool) < 4:
        st.warning(t("need_4_words"))

    # ══════════════════════════════════════════════════════════════════════════
    # MODE A — MULTIPLE CHOICE
    # ══════════════════════════════════════════════════════════════════════════
    elif quiz_mode == "multiple_choice":
        col_start,col_reset=st.columns([2,1])
        with col_start:
            if st.button(t("btn_start_quiz"), use_container_width=True, type="primary"):
                q_words=quiz_pool.copy(); random.shuffle(q_words)
                st.session_state.quiz_words=q_words; st.session_state.quiz_index=0
                st.session_state.quiz_score={"correct":0,"wrong":0}; st.session_state.quiz_failed=[]
                st.session_state.quiz_answer=None; st.session_state.quiz_done=False; st.rerun()
        with col_reset:
            total_q=st.session_state.quiz_score["correct"]+st.session_state.quiz_score["wrong"]
            if total_q>0:
                pct=int(100*st.session_state.quiz_score["correct"]/total_q)
                st.metric("Score",f"{st.session_state.quiz_score['correct']}/{total_q}  ({pct}%)")
        st.markdown("---")
        if st.session_state.quiz_done:
            total_q=st.session_state.quiz_score["correct"]+st.session_state.quiz_score["wrong"]
            pct=int(100*st.session_state.quiz_score["correct"]/total_q) if total_q else 0
            st.markdown(t("quiz_complete"))
            st.markdown(t("quiz_score", correct=st.session_state.quiz_score['correct'], total=total_q, pct=pct))
            failed=st.session_state.quiz_failed
            if failed:
                st.markdown(t("words_to_review", n=len(failed)))
                for fw in failed: fd=cache.get(fw,{}); st.markdown(f"- **{fw}** — {loc(fd, 'translation')}")
                st.markdown("---")
                if st.button(t("btn_export_failed"), use_container_width=True):
                    with st.spinner(t("building_doc")):
                        buf=build_word_doc(failed,all_words,{"pos":True,"translation":True,"definition":True,"example":True})
                    st.download_button(label=t("download_failed"),data=buf,file_name="failed_words.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
            else: st.success(t("perfect_score"))
        elif st.session_state.quiz_words:
            qi=st.session_state.quiz_index; qwords=st.session_state.quiz_words
            if qi>=len(qwords): st.session_state.quiz_done=True; st.rerun()
            qword=qwords[qi]; qdata=cache[qword]; correct_tr=loc(qdata, "translation")
            choice_key=f"quiz_choices_{qi}"
            if choice_key not in st.session_state:
                qpos=qdata.get("part_of_speech","")
                same_pos=[w for w in quiz_pool if w!=qword and cache[w].get("part_of_speech","")==qpos]
                wrong_pool=same_pos if len(same_pos)>=3 else [w for w in quiz_pool if w!=qword]
                # Shuffle wrong pool and pick distractors, skipping any that share the correct translation
                random.shuffle(wrong_pool)
                wrong_translations=[]
                for ww in wrong_pool:
                    tr=loc(cache[ww], "translation")
                    if tr!=correct_tr and tr not in wrong_translations:
                        wrong_translations.append(tr)
                    if len(wrong_translations)==3: break
                choices=wrong_translations[:]
                insert_pos=random.randint(0,len(choices))
                choices.insert(insert_pos,correct_tr)
                st.session_state[choice_key]=choices
            choices=st.session_state[choice_key]
            st.markdown(f"<p class='progress-text'>{t('question_progress', current=qi+1, total=len(qwords))}</p>", unsafe_allow_html=True); st.progress(qi/len(qwords))
            answered=st.session_state.quiz_answer
            qw_safe=_html.escape(qword); qex=_html.escape(qdata.get("example_greek",""))
            qex_en=_html.escape(loc(qdata, "example_english", ""))
            if answered is None:
                q_html=('<div class="card" style="min-height:200px;">'+f'<div class="greek-word">{qw_safe}</div>'+f'<div class="transliteration">[ {_html.escape(qdata.get("transliteration","--"))} ]</div>'+(f'<hr class="example-divider"><div class="example-greek"><span style="font-size:0.8rem;opacity:0.6;">Παράδειγμα</span><br>{qex}</div>' if qex else '')+'</div>')
            else:
                qpos_s=_html.escape(qdata.get("part_of_speech","--")); qdif_s=_html.escape(qdata.get("difficulty","?"))
                qg, qa = get_gender_info(qdata)
                qgender_html = f'<span class="gender-badge">{qa} ({qg})</span>' if qg else ""
                q_html=('<div class="card" style="min-height:200px;">'+f'<span class="pos-badge">{qpos_s}</span>'+f'<span class="diff-badge">{qdif_s}</span>'+f'{qgender_html}'+f'<div class="greek-word">{qw_safe}</div>'+f'<div class="transliteration">[ {_html.escape(qdata.get("transliteration","--"))} ]</div>')
            st.markdown(q_html, unsafe_allow_html=True); st.markdown("<br>", unsafe_allow_html=True)
            if answered is None:
                st.markdown(t("choose_translation")); cols=st.columns(2); labels=["A","B","C","D"]
                for ci,choice in enumerate(choices):
                    with cols[ci%2]:
                        if st.button(f"{labels[ci]})  {choice}", key=f"q_{qi}_{ci}", use_container_width=True):
                            st.session_state.quiz_answer=choice
                            if choice==correct_tr: st.session_state.quiz_score["correct"]+=1
                            else:
                                st.session_state.quiz_score["wrong"]+=1
                                if qword not in st.session_state.quiz_failed: st.session_state.quiz_failed.append(qword)
                            st.rerun()
            else:
                qpos=qdata.get("part_of_speech","--"); qdif=qdata.get("difficulty","?")
                if answered==correct_tr: st.success(t("correct_answer", tr=correct_tr, pos=qpos, diff=qdif))
                else: st.error(t("wrong_answer", chosen=answered)); st.markdown(t("correct_was", tr=correct_tr, pos=qpos, diff=qdif))
                st.markdown("<br>", unsafe_allow_html=True)
                nb1,nb2=st.columns([2,1])
                with nb1:
                    if st.button(t("btn_next_question"), use_container_width=True, type="primary"):
                        st.session_state.quiz_index+=1; st.session_state.quiz_answer=None
                        if st.session_state.quiz_index>=len(qwords): st.session_state.quiz_done=True
                        st.rerun()
                with nb2:
                     if st.button(t("btn_exit_quiz"), use_container_width=True): st.session_state.quiz_done=True; st.rerun()
                if st.session_state.quiz_failed:
                    with st.expander(t("export_failed_so_far", n=len(st.session_state.quiz_failed))):
                        if st.button(t("btn_generate_word"), key="mid_export", use_container_width=True):
                            with st.spinner(t("building_doc_short")):
                                buf=build_word_doc(st.session_state.quiz_failed,all_words,{"pos":True,"translation":True,"definition":True,"example":True})
                            st.download_button(label="⬇️ Download failed_words.docx",data=buf,file_name="failed_words.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True,key="mid_dl")
        else: st.info(t("press_start_quiz"))

    # ══════════════════════════════════════════════════════════════════════════
    # MODE B — LISTEN & TYPE
    # ══════════════════════════════════════════════════════════════════════════
    else:
        # ── Settings & start ─────────────────────────────────────────────────
        lt_pool = [w for w in quiz_pool if w in cache]
        cfg_col, score_col = st.columns([2,1])
        with cfg_col:
            lt_target = st.radio(t("listen_to"), [t("listen_word"), t("listen_example")],
                                 horizontal=True, key="lt_target_radio")
            target_key = "word" if lt_target == t("listen_word") else "example"
        with score_col:
            lt_total = st.session_state.lt_score["correct"] + st.session_state.lt_score["wrong"]
            if lt_total > 0:
                lt_pct = int(100 * st.session_state.lt_score["correct"] / lt_total)
                st.metric("Score", f"{st.session_state.lt_score['correct']}/{lt_total}  ({lt_pct}%)")

        if st.button(t("btn_start_listen"), use_container_width=True, type="primary"):
            lt_words = lt_pool.copy()
            if target_key == "example":
                lt_words = [w for w in lt_words if cache[w].get("example_greek","")]
            random.shuffle(lt_words)
            st.session_state.lt_words     = lt_words
            st.session_state.lt_index     = 0
            st.session_state.lt_score     = {"correct":0,"wrong":0}
            st.session_state.lt_failed    = []
            st.session_state.lt_done      = False
            st.session_state.lt_submitted = False
            st.session_state["lt_target"] = target_key
            st.rerun()

        st.markdown("---")

        # ── Done screen ───────────────────────────────────────────────────────
        if st.session_state.lt_done:
            lt_total = st.session_state.lt_score["correct"] + st.session_state.lt_score["wrong"]
            lt_pct   = int(100 * st.session_state.lt_score["correct"] / lt_total) if lt_total else 0
            st.markdown(t("listen_complete"))
            st.markdown(t("quiz_score", correct=st.session_state.lt_score['correct'], total=lt_total, pct=lt_pct))
            failed = st.session_state.lt_failed
            if failed:
                st.markdown(t("words_to_review", n=len(failed)))
                for fw in failed:
                    fd = cache.get(fw, {})
                    st.markdown(f"- **{fw}** — {loc(fd, 'translation')}")
                if st.button(t("btn_export_failed"), use_container_width=True, key="lt_export"):
                    with st.spinner(t("building_doc")):
                        buf = build_word_doc(failed, all_words,
                                             {"pos":True,"translation":True,"definition":True,"example":True})
                    st.download_button(label=t("download_failed"), data=buf,
                                       file_name="lt_failed_words.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True, key="lt_dl")
            else:
                st.success(t("perfect_score"))

        # ── Active quiz ───────────────────────────────────────────────────────
        elif st.session_state.lt_words:
            li      = st.session_state.lt_index
            lwords  = st.session_state.lt_words
            ltgt    = st.session_state.get("lt_target", "word")

            if li >= len(lwords):
                st.session_state.lt_done = True; st.rerun()

            lword = lwords[li]
            ldata = cache[lword]
            correct_text = lword if ltgt == "word" else ldata.get("example_greek", lword)

            st.markdown(f"<p class='progress-text'>Question {li+1} of {len(lwords)}</p>",
                        unsafe_allow_html=True)
            st.progress(li / len(lwords))

            # Ensure audio exists
            with st.spinner("Preparing audio…"):
                w_path, e_path = _ensure_audio(lword, ldata)
            audio_path = w_path if ltgt == "word" else e_path

            # Audio card
            target_label = t("listen_word") if ltgt == "word" else t("listen_example")
            st.markdown(f"<div class='card' style='min-height:160px;'>"
                        f"<div style='color:#a0aec0;font-size:0.9rem;margin-bottom:12px;'>{t('listen_and_type', target=target_label)}</div>"
                        f"<div style='color:#718096;font-size:0.8rem;'>{t('press_play_hint')}</div>"
                        f"</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            from modules.audio import read_audio
            audio_bytes = read_audio(audio_path)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.warning(t("audio_not_available"))

            submitted = st.session_state.lt_submitted

            if not submitted:
                user_ans = st.text_input(
                    t("type_greek", target=target_label),
                    key=f"lt_input_{li}",
                    placeholder=t("type_placeholder")
                )
                sc1, sc2 = st.columns([2,1])
                with sc1:
                    if st.button(t("btn_submit"), use_container_width=True, type="primary",
                                 disabled=not user_ans.strip()):
                        result, msg = _score_answer(user_ans, correct_text)
                        st.session_state[f"lt_ans_{li}"]  = user_ans
                        st.session_state[f"lt_res_{li}"]  = (result, msg)
                        if result in ("correct", "close"):
                            st.session_state.lt_score["correct"] += 1
                        else:
                            st.session_state.lt_score["wrong"] += 1
                            if lword not in st.session_state.lt_failed:
                                st.session_state.lt_failed.append(lword)
                        st.session_state.lt_submitted = True
                        st.rerun()
                with sc2:
                    if st.button(t("btn_exit"), use_container_width=True):
                        st.session_state.lt_done = True; st.rerun()
            else:
                # Show result
                user_ans          = st.session_state.get(f"lt_ans_{li}", "")
                result, msg       = st.session_state.get(f"lt_res_{li}", ("wrong",""))
                pos  = ldata.get("part_of_speech","--")
                diff = ldata.get("difficulty","?")
                tr   = loc(ldata, "translation")

                if result == "correct":
                    st.success(t("answer_correct", msg=msg, word=correct_text))
                elif result == "close":
                    st.warning(t("answer_close", msg=msg, typed=user_ans, word=correct_text))
                else:
                    st.error(t("answer_wrong", typed=user_ans))
                    st.markdown(f"{t('correct_label')} **{correct_text}**")

                # Always show full card after answer
                lw_safe = _html.escape(lword)
                ltr_safe = _html.escape(tr)
                lpos_safe = _html.escape(pos)
                ldif_safe = _html.escape(diff)
                ltrans_safe = _html.escape(ldata.get("transliteration","--"))
                lex = _html.escape(ldata.get("example_greek",""))
                lexen = _html.escape(loc(ldata, "example_english", ""))
                reveal_html = (
                    '<div class="card card-back" style="min-height:160px;margin-top:12px;">'
                    f'<span class="pos-badge">{lpos_safe}</span>'
                    f'<span class="diff-badge">{ldif_safe}</span>'
                    f'<div class="greek-word" style="font-size:2rem;">{lw_safe}</div>'
                    f'<div class="transliteration">[ {ltrans_safe} ]</div>'
                    f'<div class="translation">{ltr_safe}</div>'
                    + (f'<hr class="example-divider"><div class="example-greek">{lex}</div>'
                       f'<div class="example-en" style="display:block;margin-top:6px;">{lexen}</div>' if lex else '')
                    + '</div>'
                )
                st.markdown(reveal_html, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                nb1, nb2 = st.columns([2,1])
                with nb1:
                    if st.button(t("btn_next_listen"), use_container_width=True, type="primary", key="lt_next"):
                        st.session_state.lt_index    += 1
                        st.session_state.lt_submitted = False
                        if st.session_state.lt_index >= len(lwords):
                            st.session_state.lt_done = True
                        st.rerun()
                with nb2:
                    if st.button(t("btn_exit_quiz2"), use_container_width=True, key="lt_exit"):
                        st.session_state.lt_done = True; st.rerun()
        else:
            st.info(t("press_start_listen"))

st.markdown("---")
st.markdown(f"<p style='text-align:center;color:#4a5568;font-size:0.8rem;'>{t('footer')}</p>", unsafe_allow_html=True)