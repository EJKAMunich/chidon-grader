#!/usr/bin/env python3
"""
Chidon HaTanach Grader - Streamlit UI v4
Pages: Home | Grader | File Converter
Languages: English, Deutsch, Russian
"""

import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import json
import tempfile
import io
from pathlib import Path

from i18n import t
from templates import generate_key_template

SCRIPT_DIR = Path(__file__).resolve().parent

STAGES = [
    ("stage1.py", "Stage 1: Auto-scoring T/F & MC"),
    ("stage2.py", "Stage 2: Preparing AI grading cards"),
    ("stage3.py", "Stage 3: AI grading open questions"),
    ("stage4.py", "Stage 4: Calculating totals"),
    ("stage5.py", "Stage 5: Generating Word documents"),
]

LANG_MAP = {"English": "en", "Deutsch": "de", "Russian": "ru"}


# ---------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------

def L():
    return st.session_state.get("_lang", "en")

def T(key):
    return t(key, L())

def get_api_key():
    return st.session_state.get("_api_key", "")


def validate_key_df(df):
    errors, warnings = [], []
    required = {"Number", "Question", "Answer", "Points"}
    missing = required - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {', '.join(missing)}")
        return False, warnings, errors
    if df["Number"].nunique() != len(df):
        errors.append("Duplicate question numbers")
    n = len(df)
    if n < 10:
        warnings.append(f"Only {n} questions")
    tf = df["Answer"].astype(str).isin(["T", "F"]).sum()
    mc = df["Answer"].astype(str).isin(["A", "B", "C", "D"]).sum()
    if n - tf - mc == 0:
        warnings.append("No open questions - AI grading will be skipped")
    return len(errors) == 0, warnings, errors


def validate_answers_df(df):
    errors, warnings = [], []
    required = {"Name", "Surname", "Language"}
    missing = required - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {', '.join(missing)}")
        return False, warnings, errors
    q_cols = [c for c in df.columns if c.startswith("Q") and c[1:].isdigit()]
    if not q_cols:
        errors.append("No question columns (Q1, Q2, ...)")
        return False, warnings, errors
    if len(df) == 0:
        errors.append("No participants")
    empty = df["Name"].isna().sum()
    if empty > 0:
        warnings.append(f"{empty} rows with empty names")
    return len(errors) == 0, warnings, errors


def show_data_summary(key_df, ans_df):
    n = len(key_df)
    tf = key_df["Answer"].astype(str).isin(["T", "F"]).sum()
    mc = key_df["Answer"].astype(str).isin(["A", "B", "C", "D"]).sum()
    op = n - tf - mc

    c1, c2, c3 = st.columns(3)
    c1.metric(T("questions"), n)
    c2.metric(T("max_score"), int(key_df["Points"].sum()))
    c3.metric(T("participants"), len(ans_df))

    c1, c2, c3 = st.columns(3)
    c1.metric(T("true_false"), int(tf))
    c2.metric(T("multiple_choice"), int(mc))
    c3.metric(T("open"), int(op))

    langs = ans_df["Language"].value_counts()
    st.caption(f"{T('languages')}: {', '.join(f'{l} ({c})' for l, c in langs.items())}")
    has_comments = key_df["Comment"].notna().sum() if "Comment" in key_df.columns else 0
    if has_comments:
        st.caption(f"{T('special_rules')}: {has_comments}")

    with st.expander(f"{T('grader_key_label')} (first 5)"):
        st.dataframe(key_df.head(), use_container_width=True, hide_index=True)
    with st.expander(f"{T('grader_ans_label')} (first 5)"):
        pcols = ["Name", "Surname", "Language"] + [c for c in ans_df.columns if c.startswith("Q")]
        preview = ans_df[[c for c in pcols if c in ans_df.columns]].head()
        if "Name" in preview.columns and "Surname" in preview.columns:
            preview = preview.copy()
            preview.index = (preview["Name"].fillna("") + " " + preview["Surname"].fillna("")).str.strip()
            preview.index.name = "Participant"
        st.dataframe(preview, use_container_width=True)


def df_to_xlsx_bytes(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def run_pipeline(work_dir, api_key, progress_bar, status_area):
    env = os.environ.copy()
    env["CHIDON_API_KEY"] = api_key
    env["ANTHROPIC_API_KEY"] = api_key
    env["CHIDON_PROVIDER"] = st.session_state.get("_provider", "anthropic")
    env["CHIDON_MODEL"] = st.session_state.get("_model", "claude-sonnet-4-5-20250929")
    base_url = os.environ.get("OPENAI_COMPAT_BASE_URL", "")
    if base_url:
        env["OPENAI_COMPAT_BASE_URL"] = base_url
    log = []
    for i, (script, desc) in enumerate(STAGES):
        progress_bar.progress(i / len(STAGES), text=f"{desc}...")
        status_area.info(desc)
        src = SCRIPT_DIR / script
        if not src.exists():
            status_area.error(f"Script not found: {script}")
            log.append(f"Missing: {script}")
            return False, "\n".join(log)
        r = subprocess.run([sys.executable, str(src)], cwd=work_dir,
                           capture_output=True, text=True, env=env, timeout=900)
        log.append(f"=== {desc} ===")
        if r.stdout: log.append(r.stdout)
        if r.stderr: log.append(f"STDERR: {r.stderr}")
        if r.returncode != 0:
            status_area.error(f"{desc} failed!")
            log.append(f"EXIT CODE: {r.returncode}")
            return False, "\n".join(log)
    progress_bar.progress(1.0, text="Done!")
    status_area.success("All stages completed.")
    return True, "\n".join(log)


def show_results(work_dir):
    path = os.path.join(work_dir, "stage4_totals.json")
    if not os.path.exists(path):
        st.warning("Results not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        totals = json.load(f)
    mx = totals["max_scores"]
    results = totals["results"]

    st.subheader(f"{T('ranking')} ({len(results)} {T('participants').lower()})")
    scores = [r["grand_total"] for r in results]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T("max_possible"), mx["total"])
    c2.metric(T("highest"), max(scores))
    c3.metric(T("average"), f"{sum(scores)/len(scores):.0f}")
    c4.metric(T("lowest"), min(scores))

    table = [{
        "Rank": r["rank"], "Name": r["full_name"], "Lang": r["language"],
        "T/F": f"{r['tf_total']}/{mx['tf']}", "MC": f"{r['mc_total']}/{mx['mc']}",
        "Open": f"{r['open_total']}/{mx['open']}", "Total": f"{r['grand_total']}/{mx['total']}",
    } for r in results]
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True,
                 height=min(400, 35 * len(results) + 38))

    st.subheader(T("download"))
    c1, c2 = st.columns(2)
    for col, fn, lbl in [(c1, "ranking.docx", "Ranking (Word)"),
                          (c2, "report_cards.docx", "Report Cards (Word)")]:
        fp = os.path.join(work_dir, fn)
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                col.download_button(lbl, f.read(), file_name=fn, type="primary")


def execute_grading(key_df, ans_df, api_key, tag=""):
    if not api_key:
        st.warning("⚠️ Enter your API key in the sidebar to run grading.")
        return
    if st.button(T("grader_run"), type="primary", use_container_width=True, key=f"run_{tag}"):
        work_dir = tempfile.mkdtemp(prefix="chidon_")
        st.session_state.work_dir = work_dir
        st.session_state.pipeline_done = False
        key_df.to_excel(os.path.join(work_dir, "Key.xlsx"), index=False)
        ans_df.to_excel(os.path.join(work_dir, "Answers.xlsx"), index=False)
        progress = st.progress(0, text="Starting...")
        status = st.empty()
        try:
            ok, log = run_pipeline(work_dir, api_key, progress, status)
        except subprocess.TimeoutExpired:
            st.error(T("grader_timeout"))
            ok, log = False, "Timeout"
        except Exception as e:
            st.error(f"Error: {e}")
            ok, log = False, str(e)
        with st.expander(T("grader_exec_log")):
            st.code(log, language="text")
        if ok:
            st.session_state.pipeline_done = True
        else:
            st.error(T("grader_failed"))

    if st.session_state.get("pipeline_done") and st.session_state.get("work_dir"):
        st.divider()
        st.header(T("grader_results"))
        show_results(st.session_state.work_dir)


# ---------------------------------------------------------------
# PAGE: HOME
# ---------------------------------------------------------------

def page_home():
    # --- Orbital animation hub (elliptical, 1/3 viewport) ---
    import streamlit.components.v1 as components

    orbital_html = f"""
    <!DOCTYPE html><html><head><style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    html,body{{width:100%;height:100%;background:transparent;overflow:hidden;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#e2e8f0}}

    /* All orbits/text centered at 60% down instead of 50% */
    :root{{--cx:50%;--cy:60%}}

    .hub{{position:relative;width:100%;height:100%}}

    /* Elliptical rings */
    .er{{position:absolute;border-radius:50%;top:var(--cy);left:var(--cx);border:1.5px solid rgba(59,130,246,0.25)}}
    .e1{{width:500px;height:140px;margin:-70px 0 0 -250px;animation:s1 30s linear infinite}}
    .e2{{width:650px;height:190px;margin:-95px 0 0 -325px;border-width:1px;border-color:rgba(59,130,246,0.15);animation:s2 42s linear infinite reverse}}
    .e3{{width:800px;height:230px;margin:-115px 0 0 -400px;border-width:1px;border-style:dashed;border-color:rgba(59,130,246,0.09);animation:s3 56s linear infinite}}

    @keyframes s1{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}
    @keyframes s2{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}
    @keyframes s3{{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}

    /* Dots */
    .ed{{position:absolute;border-radius:50%}}
    @keyframes o1{{
        0%  {{top:var(--cy);left:var(--cx);transform:translate(250px,-4px)}}
        25% {{top:var(--cy);left:var(--cx);transform:translate(0,-74px)}}
        50% {{top:var(--cy);left:var(--cx);transform:translate(-250px,-4px)}}
        75% {{top:var(--cy);left:var(--cx);transform:translate(0,66px)}}
        100%{{top:var(--cy);left:var(--cx);transform:translate(250px,-4px)}}
    }}
    @keyframes o2{{
        0%  {{top:var(--cy);left:var(--cx);transform:translate(325px,-4px)}}
        25% {{top:var(--cy);left:var(--cx);transform:translate(0,-99px)}}
        50% {{top:var(--cy);left:var(--cx);transform:translate(-325px,-4px)}}
        75% {{top:var(--cy);left:var(--cx);transform:translate(0,91px)}}
        100%{{top:var(--cy);left:var(--cx);transform:translate(325px,-4px)}}
    }}
    @keyframes o3{{
        0%  {{top:var(--cy);left:var(--cx);transform:translate(400px,-4px)}}
        25% {{top:var(--cy);left:var(--cx);transform:translate(0,-119px)}}
        50% {{top:var(--cy);left:var(--cx);transform:translate(-400px,-4px)}}
        75% {{top:var(--cy);left:var(--cx);transform:translate(0,111px)}}
        100%{{top:var(--cy);left:var(--cx);transform:translate(400px,-4px)}}
    }}

    .d1{{width:7px;height:7px;background:#3b82f6;box-shadow:0 0 10px rgba(59,130,246,.7);animation:o1 26s linear infinite}}
    .d2{{width:5px;height:5px;background:#60a5fa;box-shadow:0 0 7px rgba(96,165,250,.5);animation:o1 26s linear infinite;animation-delay:-13s}}
    .d3{{width:9px;height:9px;background:#2563eb;box-shadow:0 0 14px rgba(37,99,235,.5);animation:o2 36s linear infinite reverse}}
    .d4{{width:4px;height:4px;background:#93c5fd;box-shadow:0 0 5px rgba(147,197,253,.5);animation:o2 36s linear infinite reverse;animation-delay:-18s}}
    .d5{{width:6px;height:6px;background:#14b8a6;box-shadow:0 0 9px rgba(20,184,166,.5);animation:o2 36s linear infinite reverse;animation-delay:-9s}}
    .d6{{width:6px;height:6px;background:#3b82f6;box-shadow:0 0 8px rgba(59,130,246,.4);animation:o3 50s linear infinite}}
    .d7{{width:4px;height:4px;background:#60a5fa;box-shadow:0 0 5px rgba(96,165,250,.4);animation:o3 50s linear infinite;animation-delay:-25s}}
    .d8{{width:5px;height:5px;background:#14b8a6;box-shadow:0 0 7px rgba(20,184,166,.4);animation:o3 50s linear infinite;animation-delay:-37s}}

    /* Glow */
    .gw{{position:absolute;width:260px;height:100px;top:var(--cy);left:var(--cx);margin:-50px 0 0 -130px;
        background:radial-gradient(ellipse,rgba(59,130,246,.14) 0%,transparent 70%);animation:gp 4s ease-in-out infinite}}
    @keyframes gp{{0%,100%{{opacity:.5;transform:scale(1)}}50%{{opacity:.8;transform:scale(1.06)}}}}

    /* Center text */
    .tx{{position:absolute;top:var(--cy);left:var(--cx);transform:translate(-50%,-50%);z-index:10;text-align:center;white-space:nowrap}}
    .tx h1{{font-size:2.2rem;font-weight:800;color:#e2e8f0;letter-spacing:.5px;margin:0;
        text-shadow:0 0 25px rgba(59,130,246,.4),0 0 50px rgba(59,130,246,.12)}}
    .tx p{{font-size:0.88rem;color:#93c5fd;font-weight:500;margin:4px 0 0;
        text-shadow:0 0 8px rgba(96,165,250,.25)}}

    /* Floating labels */
    .lb{{position:absolute;font-size:0.6rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;pointer-events:none;opacity:0.5}}
    @keyframes b1{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}
    @keyframes b2{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(4px)}}}}

    .lt{{top:18%;left:50%;transform:translateX(-50%);color:#60a5fa;opacity:0.7;font-size:0.68rem;
         text-shadow:0 0 8px rgba(96,165,250,.4);animation:b1 3.5s ease-in-out infinite}}
    .lr{{top:60%;right:12px;transform:translateY(-50%);color:#94a3b8;animation:b2 4s ease-in-out infinite}}
    .lb2{{top:88%;left:50%;transform:translateX(-50%);color:#5eead4;opacity:0.6;font-size:0.68rem;
         text-shadow:0 0 6px rgba(20,184,166,.3);animation:b1 4.5s ease-in-out infinite;animation-delay:-1s}}
    .ll{{top:60%;left:12px;transform:translateY(-50%);color:#94a3b8;animation:b2 3.8s ease-in-out infinite;animation-delay:-2s}}
    </style></head><body>
    <div class="hub">
        <div class="er e1"></div>
        <div class="er e2"></div>
        <div class="er e3"></div>
        <div class="ed d1"></div><div class="ed d2"></div>
        <div class="ed d3"></div><div class="ed d4"></div>
        <div class="ed d5"></div><div class="ed d6"></div>
        <div class="ed d7"></div><div class="ed d8"></div>
        <div class="gw"></div>
        <div class="tx">
            <h1>Chidon HaTanach</h1>
            <p>{T("home_subtitle")}</p>
        </div>
        <div class="lb lt">{T("nav_grader")}</div>
        <div class="lb lr">{T("home_formats_title")}</div>
        <div class="lb lb2">{T("nav_converter")}</div>
        <div class="lb ll">Template</div>
    </div>
    </body></html>
    """
    components.html(orbital_html, height=300, scrolling=False)

    # --- Action buttons ---
    _, c1, c2, _ = st.columns([1, 1.2, 1.2, 1])
    with c1:
        if st.button(T("nav_converter"), key="orb_conv", use_container_width=True):
            st.session_state.page = "converter"
            st.rerun()
    with c2:
        if st.button(f"{T('nav_grader')}", key="orb_grade", type="primary", use_container_width=True):
            st.session_state.page = "grader"
            st.rerun()

    # --- Always-visible info blocks (2/3 of viewport) ---
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.subheader(T("home_what_title"))
    st.write(T("home_what_text"))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div style="padding:16px 20px;
            background:rgba(59,130,246,0.08);
            border-left:4px solid #3b82f6; border-radius:10px; border:1px solid rgba(59,130,246,0.15);
            border-left:4px solid #3b82f6; margin-bottom:12px;">
            <p style="margin:0 0 8px 0; font-size:1.05rem; color:#93c5fd; font-weight:700;">A — {T('home_step1_title')}</p>
            <p style="margin:0 0 10px 0; font-size:0.88rem; color:#cbd5e1; line-height:1.5;">{T('home_step1_text')}</p>
            <div style="margin-top:10px; padding:10px 14px; background:rgba(59,130,246,0.06);
                border-radius:8px; border:1px solid rgba(59,130,246,0.12);">
                <p style="margin:0; font-size:0.85rem; color:#93c5fd; font-weight:600;">{T('home_key_format_title')}</p>
                <p style="margin:4px 0 0; font-size:0.82rem; color:#94a3b8; line-height:1.4;">{T('home_key_format_text')}</p>
            </div>
        </div>""", unsafe_allow_html=True)
        st.download_button(
            T("home_download_template"),
            data=generate_key_template(),
            file_name="Key_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        st.markdown(f"""<div style="padding:16px 20px;
            background:rgba(20,184,166,0.08);
            border-left:4px solid #14b8a6; border-radius:10px; border:1px solid rgba(20,184,166,0.15);
            border-left:4px solid #14b8a6;">
            <p style="margin:0 0 8px 0; font-size:1.05rem; color:#5eead4; font-weight:700;">B — {T('home_step2_title')}</p>
            <p style="margin:0 0 10px 0; font-size:0.88rem; color:#cbd5e1; line-height:1.5;">{T('home_step2_text')}</p>
            <div style="margin-top:10px; padding:10px 14px; background:rgba(20,184,166,0.06);
                border-radius:8px; border:1px solid rgba(20,184,166,0.12);">
                <p style="margin:0; font-size:0.85rem; color:#5eead4; font-weight:600;">{T('home_ans_format_title')}</p>
                <p style="margin:4px 0 0; font-size:0.82rem; color:#94a3b8; line-height:1.4;">{T('home_ans_format_text')}</p>
            </div>
        </div>""", unsafe_allow_html=True)




# ---------------------------------------------------------------
# PAGE: GRADER
# ---------------------------------------------------------------

def page_grader():
    st.header(T("grader_title"))
    api_key = get_api_key()

    from_conv = (st.session_state.get("grader_key_df") is not None and
                 st.session_state.get("grader_ans_df") is not None)

    if from_conv:
        st.success(T("grader_from_converter"))
        key_df = st.session_state.grader_key_df
        ans_df = st.session_state.grader_ans_df
        if st.button(T("grader_clear"), key="clear_conv"):
            st.session_state.grader_key_df = None
            st.session_state.grader_ans_df = None
            st.rerun()
    else:
        st.caption(T("grader_upload_hint"))
        c1, c2 = st.columns(2)
        with c1:
            key_file = st.file_uploader(T("grader_key_label"), type=["xlsx"], key="g_key",
                                        help="Number | Question | Answer | Points | Comment")
        with c2:
            ans_file = st.file_uploader(T("grader_ans_label"), type=["xlsx"], key="g_ans",
                                        help="Name | Surname | Language | Q1 | Q2 | ... | Q50")
        if not key_file or not ans_file:
            st.info(T("grader_upload_both"))
            return
        try:
            key_df = pd.read_excel(key_file)
            ans_df = pd.read_excel(ans_file)
        except Exception as e:
            st.error(f"Error reading files: {e}")
            return

    key_ok, kw, ke = validate_key_df(key_df)
    ans_ok, aw, ae = validate_answers_df(ans_df)
    for e in ke + ae: st.error(e)
    for w in kw + aw: st.warning(w)
    if not key_ok or not ans_ok:
        st.error(T("fix_errors"))
        return

    st.subheader(T("grader_preview"))
    show_data_summary(key_df, ans_df)
    st.divider()

    if not api_key:
        st.warning(T("grader_no_key"))
        return

    execute_grading(key_df, ans_df, api_key, tag="grader")


# ---------------------------------------------------------------
# PAGE: FILE CONVERTER
# ---------------------------------------------------------------

def page_converter():
    st.header(T("conv_title"))
    st.caption(T("conv_desc"))

    api_key = get_api_key()
    if not api_key:
        st.warning(T("grader_no_key"))
        return

    tab_key, tab_ans = st.tabs([T("conv_tab_key"), T("conv_tab_ans")])
    with tab_key:
        _converter_block("key", api_key)
    with tab_ans:
        _converter_block("answers", api_key)

    st.divider()
    _send_to_grader_section()


def _check_file_type_mismatch(filepath, file_type):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in (".xlsx", ".xls", ".csv", ".tsv"):
            return
        df = pd.read_excel(filepath, dtype=str, nrows=5) if ext in (".xlsx", ".xls") \
            else pd.read_csv(filepath, dtype=str, nrows=5)
        cols = df.columns.tolist()
        if file_type == "key":
            long_h = sum(1 for c in cols if len(str(c)) > 60)
            if long_h > 5 or len(cols) > 20:
                st.warning(T("conv_mismatch_key"))
        else:
            key_cols = {"number", "question", "answer", "points", "comment",
                        "frage", "antwort", "punkte", "nummer"}
            found = sum(1 for c in cols if str(c).lower().strip() in key_cols)
            if found >= 3 and len(cols) < 10:
                st.warning(T("conv_mismatch_ans"))
    except Exception:
        pass


def _converter_block(file_type, api_key):
    label = T("grader_key_label") if file_type == "key" else T("grader_ans_label")
    prefix = f"conv_{file_type}"
    df_key = f"{prefix}_df"
    map_key = f"{prefix}_map"
    edited_key = f"{prefix}_edited"

    st.subheader(f"{T('conv_upload')}: {label}")

    raw_file = st.file_uploader(
        label, type=["xlsx", "xls", "csv", "tsv", "pdf", "docx", "doc", "txt", "md"],
        key=f"{prefix}_upload", help=T("conv_upload_help"), label_visibility="collapsed",
    )

    if not raw_file:
        if st.session_state.get(df_key) is not None:
            st.info(f"{label} {T('conv_already_parsed')} ({len(st.session_state[df_key])} rows).")
            _show_editor(file_type)
        return

    if st.button(f"{T('conv_analyze')} {label.lower()}", key=f"{prefix}_parse", use_container_width=True):
        suffix = os.path.splitext(raw_file.name)[1] or ".xlsx"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        raw_file.seek(0); tmp.write(raw_file.read()); tmp.close()

        try:
            _check_file_type_mismatch(tmp.name, file_type)
        except Exception:
            pass

        from stage0 import parse_key_file, parse_answers_file
        parse_fn = parse_key_file if file_type == "key" else parse_answers_file

        with st.spinner("Analyzing..."):
            try:
                df, mapping, warnings, errors = parse_fn(tmp.name, api_key)
            except Exception as e:
                st.error(f"Parsing failed: {e}")
                os.unlink(tmp.name)
                return

        os.unlink(tmp.name)
        for e in errors: st.error(e)
        for w in warnings: st.warning(w)
        if errors:
            st.error(T("parsing_failed"))
            return

        st.session_state[df_key] = df
        st.session_state[map_key] = mapping
        st.session_state[edited_key] = None
        st.rerun()

    if st.session_state.get(df_key) is not None:
        _show_editor(file_type)


def _show_editor(file_type):
    prefix = f"conv_{file_type}"
    df_key = f"{prefix}_df"
    map_key = f"{prefix}_map"
    edited_key = f"{prefix}_edited"
    label = T("grader_key_label") if file_type == "key" else T("grader_ans_label")

    df = st.session_state[df_key]
    mapping = st.session_state.get(map_key, {})

    if file_type == "key" and "Answer" in df.columns:
        n = len(df)
        tf = df["Answer"].astype(str).isin(["T", "F"]).sum()
        mc = df["Answer"].astype(str).isin(["A", "B", "C", "D"]).sum()
        st.caption(f"{n} {T('questions').lower()} ({int(tf)} T/F, {int(mc)} MC, {int(n-tf-mc)} {T('open').lower()})")
    elif file_type == "answers":
        q_cols = [c for c in df.columns if c.startswith("Q") and c[1:].isdigit()]
        lang_str = ""
        if "Language" in df.columns:
            langs = df["Language"].value_counts()
            lang_str = ", ".join(f"{l} ({c})" for l, c in langs.items())
        st.caption(f"{len(df)} {T('participants').lower()}, {len(q_cols)} {T('questions').lower()}. {T('languages')}: {lang_str}")

    with st.expander(T("ai_mapping")):
        st.json(mapping)

    st.caption(T("conv_edit_hint"))

    if file_type == "answers" and "Name" in df.columns and "Surname" in df.columns:
        display = df.copy()
        display.index = (df["Name"].fillna("") + " " + df["Surname"].fillna("")).str.strip()
        display.index.name = "Participant"
        edited = st.data_editor(display, use_container_width=True, hide_index=False,
                                num_rows="dynamic", key=f"{prefix}_editor")
        edited = edited.reset_index(drop=True)
    else:
        edited = st.data_editor(df, use_container_width=True, hide_index=True,
                                num_rows="dynamic", key=f"{prefix}_editor")

    st.session_state[edited_key] = edited

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        fname = "Key.xlsx" if file_type == "key" else "Answers.xlsx"
        st.download_button(f"{T('conv_download')} {fname}", data=df_to_xlsx_bytes(edited),
                           file_name=fname,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with c2:
        target = "grader_key_df" if file_type == "key" else "grader_ans_df"
        if st.button(T("conv_stage"), key=f"{prefix}_stage", use_container_width=True):
            validate_fn = validate_key_df if file_type == "key" else validate_answers_df
            ok, w, e = validate_fn(edited)
            if not ok:
                for err in e: st.error(err)
                return
            st.session_state[target] = edited.copy()
            st.success(f"{label} {T('conv_staged_ok')}")
    with c3:
        if st.button(T("conv_clear"), key=f"{prefix}_clear", use_container_width=True):
            st.session_state[df_key] = None
            st.session_state[map_key] = None
            st.session_state[edited_key] = None
            target = "grader_key_df" if file_type == "key" else "grader_ans_df"
            st.session_state[target] = None
            st.rerun()


def _send_to_grader_section():
    st.subheader(T("conv_send_title"))
    key_ok = st.session_state.get("grader_key_df") is not None
    ans_ok = st.session_state.get("grader_ans_df") is not None

    c1, c2 = st.columns(2)
    key_status = T("conv_key_ready") if key_ok else T("conv_not_staged")
    ans_status = T("conv_key_ready") if ans_ok else T("conv_not_staged")
    c1.markdown(f"{T('grader_key_label')} -- **{key_status}**")
    c2.markdown(f"{T('grader_ans_label')} -- **{ans_status}**")

    if key_ok and ans_ok:
        if st.button(T("conv_go_grader"), type="primary", use_container_width=True):
            st.session_state.page = "grader"
            st.rerun()
    else:
        st.info(T("conv_stage_both"))


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------

def main():
    st.set_page_config(page_title="Chidon HaTanach Grader", page_icon="C", layout="wide")

    # ========== SPACE THEME CSS ==========
    st.markdown("""
    <style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes waveShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes starTwinkle {
        0%, 100% { opacity: 0.3; }
        50%      { opacity: 1; }
    }
    @keyframes nebulaDrift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 15px rgba(59,130,246,0.15), inset 0 0 15px rgba(59,130,246,0.05); }
        50%      { box-shadow: 0 0 25px rgba(59,130,246,0.25), inset 0 0 25px rgba(59,130,246,0.08); }
    }
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(59,130,246,0.2); }
        50%      { border-color: rgba(59,130,246,0.45); }
    }
    @keyframes cometTrail {
        0%   { transform: translateX(-100px) translateY(50px); opacity: 0; }
        10%  { opacity: 0.7; }
        90%  { opacity: 0.7; }
        100% { transform: translateX(calc(100vw + 100px)) translateY(-50px); opacity: 0; }
    }
    @keyframes orbitFloat {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }

    /* ========== STARFIELD ========== */
    .main::before, .main::after {
        content: ''; position: fixed; top:0; left:0; right:0; bottom:0;
        pointer-events: none; z-index: 0;
    }
    .main::before {
        background:
            radial-gradient(1.5px 1.5px at 10% 15%, rgba(147,197,253,0.8), transparent),
            radial-gradient(1px 1px at 25% 35%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1.5px 1.5px at 40% 10%, rgba(96,165,250,0.7), transparent),
            radial-gradient(1px 1px at 55% 45%, rgba(255,255,255,0.5), transparent),
            radial-gradient(2px 2px at 70% 20%, rgba(59,130,246,0.6), transparent),
            radial-gradient(1px 1px at 85% 55%, rgba(147,197,253,0.5), transparent),
            radial-gradient(1.5px 1.5px at 15% 70%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 35% 80%, rgba(96,165,250,0.5), transparent),
            radial-gradient(2px 2px at 60% 75%, rgba(59,130,246,0.4), transparent),
            radial-gradient(1px 1px at 80% 85%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1.5px 1.5px at 92% 40%, rgba(20,184,166,0.5), transparent),
            radial-gradient(1px 1px at 48% 60%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 5% 90%, rgba(96,165,250,0.6), transparent),
            radial-gradient(1.5px 1.5px at 75% 95%, rgba(147,197,253,0.5), transparent);
        animation: starTwinkle 4s ease-in-out infinite alternate;
    }
    .main::after {
        background:
            radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 30%, rgba(20,184,166,0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(99,102,241,0.03) 0%, transparent 50%);
        background-size: 200% 200%;
        animation: nebulaDrift 25s ease-in-out infinite;
    }

    /* Comet */
    .main .block-container::before {
        content: ''; position: fixed; top: 30%; left: -100px;
        width: 80px; height: 2px;
        background: linear-gradient(90deg, transparent, rgba(96,165,250,0.6), rgba(59,130,246,0.9), rgba(255,255,255,0.8));
        border-radius: 50%; filter: blur(0.5px);
        animation: cometTrail 12s linear infinite; animation-delay: 3s;
        pointer-events: none; z-index: 0;
    }

    /* ========== CONTENT ========== */
    .main .block-container { position: relative; z-index: 1; animation: fadeInUp 0.5s ease-out; padding-top: 1rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; min-height: 0 !important; padding: 0 !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    div[data-testid="stToolbar"] { top: 6px !important; }

    /* ========== GLASS SUBHEADERS ========== */
    .main h2 {
        padding: 10px 18px !important;
        background: rgba(17,24,39,0.6) !important;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(59,130,246,0.2);
        border-left: 4px solid #3b82f6 !important;
        border-radius: 10px !important; margin-top: 1.2rem !important;
        animation: glowPulse 5s ease-in-out infinite, fadeInUp 0.45s ease-out;
    }
    .main h3 { animation: fadeInUp 0.4s ease-out; color: #93c5fd !important; }

    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] > div {
        animation: slideInLeft 0.4s ease-out;
        background: linear-gradient(180deg, #0d1321 0%, #111827 50%, #0a0e1a 100%) !important;
        border-right: 1px solid rgba(59,130,246,0.15) !important;
    }
    section[data-testid="stSidebar"]::before {
        content: ''; position: absolute; top:0; left:0; right:0; bottom:0;
        background:
            radial-gradient(1px 1px at 20% 30%, rgba(147,197,253,0.5), transparent),
            radial-gradient(1px 1px at 60% 20%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 80% 70%, rgba(96,165,250,0.4), transparent),
            radial-gradient(1px 1px at 40% 90%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 10% 60%, rgba(20,184,166,0.3), transparent);
        pointer-events: none; z-index: 0;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
        animation: slideInLeft 0.35s ease-out both; position: relative; z-index: 1;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay: 0.03s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.06s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.09s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.12s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.15s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(6) { animation-delay: 0.18s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(7) { animation-delay: 0.21s; }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-child(8) { animation-delay: 0.24s; }

    /* Sidebar home button */
    section[data-testid="stSidebar"] button[key="home_btn"] {
        font-size: 1.3rem !important; padding: 4px 12px !important;
        background: transparent !important; border: none !important;
    }

    /* Sidebar selectboxes */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        transition: all 0.25s ease !important; border-radius: 10px !important;
        background: rgba(17,24,39,0.6) !important; border-color: rgba(59,130,246,0.2) !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 0 12px rgba(59,130,246,0.15) !important;
    }

    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        border: none !important; height: 2px !important;
        background: linear-gradient(90deg, transparent, rgba(59,130,246,0.3), rgba(96,165,250,0.6), rgba(59,130,246,0.3), transparent) !important;
        background-size: 200% 100% !important; animation: waveShift 4s ease infinite !important;
        border-radius: 2px !important; margin: 16px 0 !important;
    }
    section[data-testid="stSidebar"] h1 {
        color: #e2e8f0 !important; text-shadow: 0 0 20px rgba(59,130,246,0.3);
    }

    /* ========== MAIN DIVIDERS ========== */
    .main hr {
        border: none !important; height: 2px !important;
        background: linear-gradient(90deg, transparent, rgba(96,165,250,0.2), rgba(59,130,246,0.5), rgba(96,165,250,0.2), transparent) !important;
        background-size: 200% 100% !important; animation: waveShift 5s ease infinite !important;
        border-radius: 2px !important; margin: 24px 0 !important;
    }

    /* ========== METRIC CARDS ========== */
    div[data-testid="stMetric"] {
        background: rgba(17,24,39,0.5) !important;
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(59,130,246,0.25) !important;
        border-radius: 14px !important; padding: 16px 18px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
        animation: borderGlow 4s ease-in-out infinite;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 32px rgba(59,130,246,0.2) !important;
        border-color: rgba(59,130,246,0.5) !important;
    }
    div[data-testid="stMetric"] label { color: #93c5fd !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e2e8f0 !important; text-shadow: 0 0 8px rgba(59,130,246,0.3);
    }

    /* ========== EXPANDERS ========== */
    details[data-testid="stExpander"] {
        border: 1px solid rgba(59,130,246,0.2) !important;
        border-radius: 14px !important;
        background: rgba(17,24,39,0.4) !important;
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease !important; overflow: hidden;
    }
    details[data-testid="stExpander"]:hover {
        border-color: rgba(59,130,246,0.4) !important;
        box-shadow: 0 4px 24px rgba(59,130,246,0.12) !important;
        transform: translateY(-2px);
    }
    details[data-testid="stExpander"] summary { color: #93c5fd !important; }

    /* ========== BUTTONS ========== */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important;
        transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
        font-weight: 500 !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        backdrop-filter: blur(8px);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(59,130,246,0.25) !important;
        border-color: rgba(59,130,246,0.6) !important;
    }
    button[kind="primary"], button[data-testid="baseButton-primary"] {
        box-shadow: 0 0 20px rgba(59,130,246,0.25) !important;
    }
    button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 0 30px rgba(59,130,246,0.4), 0 6px 24px rgba(59,130,246,0.3) !important;
    }

    /* ========== FILE UPLOADER ========== */
    div[data-testid="stFileUploader"] section {
        border: 2px dashed rgba(59,130,246,0.25) !important;
        border-radius: 14px !important;
        background: rgba(17,24,39,0.3) !important;
        backdrop-filter: blur(6px); transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color: rgba(59,130,246,0.5) !important;
        background: rgba(17,24,39,0.5) !important;
        box-shadow: 0 0 24px rgba(59,130,246,0.1) !important;
    }

    /* ========== TABS ========== */
    button[data-baseweb="tab"] {
        transition: all 0.25s ease !important; border-radius: 10px 10px 0 0 !important;
    }
    button[data-baseweb="tab"]:hover { background: rgba(59,130,246,0.1) !important; color: #93c5fd !important; }
    div[data-baseweb="tab-panel"] { animation: fadeInUp 0.35s ease-out; }

    /* ========== ALERTS ========== */
    div[data-testid="stAlert"] { border-radius: 12px !important; animation: fadeInUp 0.35s ease-out; backdrop-filter: blur(6px); }

    /* ========== DATAFRAME ========== */
    div[data-testid="stDataFrame"] {
        border-radius: 14px !important; overflow: hidden;
        border: 1px solid rgba(59,130,246,0.15); transition: box-shadow 0.3s ease;
    }
    div[data-testid="stDataFrame"]:hover { box-shadow: 0 4px 24px rgba(59,130,246,0.1); }

    /* ========== TEXT INPUTS ========== */
    .stTextInput > div > div > input {
        border-radius: 10px !important; background: rgba(17,24,39,0.5) !important;
        border-color: rgba(59,130,246,0.2) !important; transition: all 0.25s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 0 16px rgba(59,130,246,0.15) !important;
    }

    /* ========== STAGGER ========== */
    .main div[data-testid="stVerticalBlock"] > div { animation: fadeInUp 0.4s ease-out both; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.04s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.08s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.12s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.16s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(6) { animation-delay: 0.20s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(7) { animation-delay: 0.24s; }
    .main div[data-testid="stVerticalBlock"] > div:nth-child(8) { animation-delay: 0.28s; }
    .main div[data-testid="stHorizontalBlock"] > div { animation: fadeInUp 0.4s ease-out both; }
    .main div[data-testid="stHorizontalBlock"] > div:nth-child(2) { animation-delay: 0.1s; }
    .main div[data-testid="stHorizontalBlock"] > div:nth-child(3) { animation-delay: 0.2s; }
    .main div[data-testid="stHorizontalBlock"] > div:nth-child(4) { animation-delay: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

    # Default state
    defaults = {
        "page": "home", "_lang": "en", "_prev_page": "home",
        "work_dir": None, "pipeline_done": False,
        "grader_key_df": None, "grader_ans_df": None,
        "conv_key_df": None, "conv_key_map": None, "conv_key_edited": None,
        "conv_answers_df": None, "conv_answers_map": None, "conv_answers_edited": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Sidebar
    with st.sidebar:
        # Home button at top
        if st.button("🏠", key="home_btn", use_container_width=False):
            st.session_state.page = "home"
            st.rerun()

        st.title(T("sidebar_title"))

        lang_name = st.selectbox(
            T("sidebar_language"),
            options=list(LANG_MAP.keys()),
            index=list(LANG_MAP.values()).index(L()),
            key="lang_select",
        )
        st.session_state["_lang"] = LANG_MAP[lang_name]

        st.divider()

        api_key = st.text_input(T("sidebar_api_key"), type="password",
                                placeholder="Your API key...", key="api_input")
        if not api_key:
            st.caption("⚠️ Enter your API key to use the Grader")
        else:
            st.caption("✅ API key set")
        st.session_state["_api_key"] = api_key

        st.divider()

        from llm_client import PROVIDERS
        provider = st.selectbox(
            T("sidebar_provider"),
            options=list(PROVIDERS.keys()),
            format_func=lambda k: PROVIDERS[k]["label"],
            index=0, key="provider_select",
        )
        info = PROVIDERS[provider]
        model = st.selectbox(
            T("sidebar_model"),
            options=[m[0] for m in info["models"]],
            format_func=lambda m: next((lb for mid, lb in info["models"] if mid == m), m),
            index=0, key="model_select",
        )
        custom = st.text_input(T("sidebar_custom_model"), value="", key="custom_model")
        model = custom.strip() if custom.strip() else model

        if provider == "openai_compat":
            base_url = st.selectbox("API Endpoint",
                                    options=["together", "groq", "openrouter", "custom"],
                                    index=0, key="compat_ep")
            if base_url == "custom":
                base_url = st.text_input("Base URL:", key="custom_url", placeholder="https://...")
            else:
                base_url = info["base_urls"][base_url]
            os.environ["OPENAI_COMPAT_BASE_URL"] = base_url or ""

        st.session_state["_provider"] = provider
        st.session_state["_model"] = model
        os.environ["CHIDON_PROVIDER"] = provider
        os.environ["CHIDON_MODEL"] = model

        st.divider()

        # Staged indicator
        key_ok = st.session_state.get("grader_key_df") is not None
        ans_ok = st.session_state.get("grader_ans_df") is not None
        if key_ok or ans_ok:
            st.divider()
            st.caption(T("sidebar_staged"))
            if key_ok: st.caption(f"  {T('sidebar_key_ready')}")
            if ans_ok: st.caption(f"  {T('sidebar_ans_ready')}")

    # Page routing with warp transition
    p = st.session_state.page
    prev = st.session_state.get("_prev_page", p)
    navigated = (prev != p)
    st.session_state["_prev_page"] = p

    if navigated:
        # Warp / hyperspace transition
        import streamlit.components.v1 as _comp
        _comp.html("""
        <style>
        @keyframes warpZoom {
            0%   { transform: scale(1); opacity:1; filter: blur(0); }
            30%  { transform: scale(0.95); opacity:0.9; filter: blur(0); }
            60%  { transform: scale(1.3); opacity:0.4; filter: blur(6px); }
            100% { transform: scale(1); opacity:0; filter: blur(0); }
        }
        @keyframes warpStar {
            0%   { transform: translate(var(--sx), var(--sy)) scale(0); opacity:0; }
            20%  { opacity:1; transform: translate(var(--sx), var(--sy)) scale(1); }
            100% { opacity:0; transform: translate(calc(var(--sx) * 6), calc(var(--sy) * 6)) scale(0.3); }
        }
        .warp-overlay {
            position:fixed; top:0; left:0; width:100vw; height:100vh;
            z-index:99999; pointer-events:none;
            animation: warpZoom 1.2s ease-in-out forwards;
            background: radial-gradient(circle at 50% 50%, rgba(59,130,246,0.15) 0%, transparent 60%);
        }
        .warp-star {
            position:absolute; top:50%; left:50%; width:3px; height:3px;
            background: white; border-radius:50%;
            animation: warpStar 1s ease-out forwards;
            box-shadow: 0 0 6px rgba(147,197,253,0.8);
        }
        </style>
        <div class="warp-overlay">
        """ + "".join([
            f'<div class="warp-star" style="--sx:{x}px;--sy:{y}px;animation-delay:{d}s"></div>'
            for x, y, d in [
                (-20,-30,0), (40,-10,0.02), (-50,20,0.04), (30,40,0.06), (-10,-50,0.08),
                (60,-30,0.1), (-40,50,0.12), (20,-60,0.14), (-60,-20,0.16), (50,30,0.18),
                (10,60,0.2), (-30,-40,0.22), (70,10,0.24), (-20,70,0.26), (40,-50,0.28),
                (-70,40,0.3), (60,60,0.05), (-50,-60,0.15), (80,-40,0.25), (-80,20,0.1),
            ]
        ]) + """
        </div>
        """, height=0, scrolling=False)

    if p == "home":
        page_home()
    elif p == "grader":
        page_grader()
    elif p == "converter":
        page_converter()


if __name__ == "__main__":
    main()
