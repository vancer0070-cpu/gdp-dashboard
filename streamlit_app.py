import math
import random

import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="재미있는 수학 교실", page_icon="🧮", layout="centered")

PI = 3.14

ROUND_SIZE = 5
PASS_MAX_WRONG = 2

LEVELS = {
    "정각": [0],
    "30분 단위": [0, 30],
    "15분 단위": [0, 15, 30, 45],
    "10분 단위": list(range(0, 60, 10)),
    "5분 단위": list(range(0, 60, 5)),
    "1분 단위": list(range(60)),
}
TIME_LEVELS = list(LEVELS)
CALC_LEVELS = ["30분 단위", "15분 단위", "1분 단위"]

SECTIONS = [
    "🔍 원리 탐구",
    "👀 시각 읽기",
    "✋ 시계 맞추기",
    "⏪ 시간 되감기",
    "➕➖ 시간 계산",
    "🏆 점수판",
]


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


def big_digital(h: int, m: int):
    st.markdown(
        f"<h1 style='text-align:center; letter-spacing:4px'>{h}:{m:02d}</h1>",
        unsafe_allow_html=True,
    )


def fmt(h: int, m: int) -> str:
    return f"{h}:{m:02d}"


def draw_circle(r: float):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.add_patch(plt.Circle((0, 0), r, fill=True, alpha=0.2, color="tab:blue", ec="tab:blue", lw=2))
    ax.plot([-r, r], [0, 0], color="tab:red", lw=2)
    ax.plot([0, 0], [0, r], color="tab:green", lw=2)
    ax.plot(0, 0, "ko")
    ax.set_xlim(-11, 11)
    ax.set_ylim(-11, 11)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig


def draw_clock(hour: int, minute: int, show_minutes: bool = False):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, lw=3))
    for n in range(1, 13):
        a = math.radians(n * 30)
        ax.text(0.8 * math.sin(a), 0.8 * math.cos(a), str(n), ha="center", va="center", fontsize=16)
    for t in range(60):
        a = math.radians(t * 6)
        L = 0.06 if t % 5 == 0 else 0.03
        ax.plot([(1 - L) * math.sin(a), math.sin(a)], [(1 - L) * math.cos(a), math.cos(a)], "k", lw=1)
        if show_minutes and t % 5 == 0 and t > 0:
            ax.text(1.13 * math.sin(a), 1.13 * math.cos(a), str(t), ha="center", va="center", fontsize=9, color="gray")
    ha = math.radians(((hour % 12) + minute / 60) * 30)
    ma = math.radians(minute * 6)
    ax.plot([0, 0.5 * math.sin(ha)], [0, 0.5 * math.cos(ha)], lw=6, color="tab:blue")
    ax.plot([0, 0.9 * math.sin(ma)], [0, 0.9 * math.cos(ma)], lw=3, color="tab:red")
    ax.plot(0, 0, "ko")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig


def read_time(h: int, m: int) -> str:
    return f"{h}시 정각" if m == 0 else f"{h}시 {m}분"


def add_time(h: int, m: int, delta: int):
    total = (h % 12) * 60 + m + delta
    return (total // 60) % 12 or 12, total % 60


def dur_text(d: int) -> str:
    hh, mm = divmod(d, 60)
    if hh == 0:
        return f"{mm}분"
    if mm == 0:
        return f"{hh}시간"
    return f"{hh}시간 {mm}분"


def minute_hint(m: int) -> str:
    if m == 0:
        return "분침(긴바늘)이 **12**를 가리켜요 → 정각이에요."
    q, r = divmod(m, 5)
    if r == 0:
        return f"분침(긴바늘)이 **{q}**를 가리켜요 → {q} × 5 = **{m}분**"
    if q == 0:
        return f"분침(긴바늘)이 12에서 **{r}칸** 더 간 곳 → **{m}분**"
    return f"분침(긴바늘)이 {q}에서 **{r}칸** 더 간 곳 → {q} × 5 + {r} = **{m}분**"


def wrong_hint(ah: int, am: int, ch: int, cm: int) -> str:
    if ah == ch:
        return "시는 맞았어요! 분을 다시 살펴볼까요?"
    if am == cm:
        return "분은 맞았어요! 시를 다시 살펴볼까요?"
    return "시와 분을 모두 다시 확인해 보세요."


def next_id() -> int:
    st.session_state["qid"] = st.session_state.get("qid", 0) + 1
    return st.session_state["qid"]


def new_round(levels: list, level_idx: int, make_q) -> dict:
    level = levels[level_idx]
    qs, seen = [], set()
    for _ in range(200):
        if len(qs) == ROUND_SIZE:
            break
        q = make_q(level)
        sig = tuple(sorted(q.items()))
        if sig not in seen:
            seen.add(sig)
            qs.append(q)
    while len(qs) < ROUND_SIZE:
        qs.append(make_q(level))
    return {
        "uid": next_id(),
        "level": level_idx,
        "qs": qs,
        "order": list(range(ROUND_SIZE)),
        "pos": 0,
        "first": [None] * ROUND_SIZE,
        "final": [None] * ROUND_SIZE,
        "answers": [None] * ROUND_SIZE,
        "phase": "ask",
        "msg": None,
        "retried": False,
        "celebrated": False,
    }


def log_round(cur: dict, title: str, levels: list):
    n = len(cur["qs"])
    first_wrong = sum(1 for r in cur["first"] if not r)
    final_wrong = sum(1 for r in cur["final"] if not r)
    rec = {
        "uid": cur["uid"],
        "활동": title,
        "단계": levels[cur["level"]],
        "처음 점수": f"{n - first_wrong}/{n}",
        "최종 점수": f"{n - final_wrong}/{n}",
        "통과": "✅" if first_wrong <= PASS_MAX_WRONG else "다시 도전",
    }
    hist = st.session_state.get("history")
    if hist is None:
        hist = []
        st.session_state["history"] = hist
    for i, old in enumerate(hist):
        if old["uid"] == cur["uid"]:
            hist[i] = rec
            return
    hist.append(rec)


def run_quiz(name, title, levels, make_q, ask, solution, explain, review=None, label=None):
    S = st.session_state
    key, sel = f"{name}_st", f"{name}_lvl"

    if key in S:
        S[sel] = levels[S[key]["level"]]
    else:
        if sel not in S:
            S[sel] = levels[0]
        S[key] = new_round(levels, levels.index(S[sel]), make_q)

    def drop():
        S.pop(key, None)

    def go(idx):
        S[sel] = levels[idx]
        S.pop(key, None)

    def retry():
        c = S[key]
        c["order"] = [i for i, ok in enumerate(c["final"]) if not ok]
        c["pos"], c["phase"], c["retried"] = 0, "ask", True

    def advance():
        c = S[key]
        if c["pos"] + 1 < len(c["order"]):
            c["pos"] += 1
            c["phase"] = "ask"
        else:
            c["phase"] = "result"
            log_round(c, title, levels)

    cur = S[key]
    li = cur["level"]
    st.selectbox("단계 선택", levels, key=sel, on_change=drop)
    st.progress((li + 1) / len(levels))
    st.caption(f"단계 {li + 1} / {len(levels)} · 한 라운드는 {ROUND_SIZE}문제예요")

    if cur["phase"] in ("ask", "feedback"):
        i = cur["order"][cur["pos"]]
        q = cur["qs"][i]
        total = len(cur["order"])
        tag = " · 다시 도전" if cur["retried"] else ""
        st.subheader(f"문제 {cur['pos'] + 1} / {total}{tag}")
        kid = f"{name}_{cur['uid']}_{i}_{int(cur['retried'])}"

        if cur["phase"] == "ask":
            ans = ask(q, levels[li], kid)
            if st.button("정답 확인", key=f"{kid}_check", type="primary"):
                ok = ans == solution(q)
                if not cur["retried"]:
                    cur["first"][i] = ok
                    cur["answers"][i] = ans
                cur["final"][i] = ok
                cur["msg"] = (ok, explain(q, ok, ans))
                cur["phase"] = "feedback"
                st.rerun()
        else:
            ok, text = cur["msg"]
            if review:
                review(q)
            (st.success if ok else st.error)(text)
            last = cur["pos"] + 1 >= total
            st.button(
                "결과 보기 ▶" if last else "다음 문제 ▶",
                key=f"{kid}_next",
                on_click=advance,
                type="primary",
            )
        return

    n = len(cur["qs"])
    first_wrong = sum(1 for r in cur["first"] if not r)
    final_wrong = sum(1 for r in cur["final"] if not r)
    passed = first_wrong <= PASS_MAX_WRONG

    st.subheader("🏆 이번 라운드 점수판")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("처음 푼 점수", f"{n - first_wrong} / {n}")
    if cur["retried"]:
        with c2:
            st.metric("다시 도전 후 점수", f"{n - final_wrong} / {n}")

    rows = []
    for i, q in enumerate(cur["qs"]):
        sol = solution(q)
        a = cur["answers"][i]
        row = {}
        if label:
            row["문제"] = label(q)
        row["정답"] = fmt(*sol)
        row["내 답"] = fmt(*a) if a else "-"
        row["처음"] = "⭕" if cur["first"][i] else "❌"
        row["다시 도전"] = "-" if cur["first"][i] else ("⭕" if cur["final"][i] else "❌")
        rows.append(row)
    st.table(rows)

    if final_wrong == 0:
        st.success("모두 맞혔어요! 정말 잘했어요 🎉")
        if not cur["celebrated"]:
            st.balloons()
            cur["celebrated"] = True
    elif passed:
        st.info(f"거의 다 맞혔어요! 틀린 {final_wrong}문제는 다시 한번 도전해 볼 수 있어요 💪")
    else:
        st.warning(f"틀린 문제가 {final_wrong}개예요. 같은 단계를 한 번 더 연습해 볼까요?")

    bkey = f"{name}_{cur['uid']}_{int(cur['retried'])}"
    if passed and final_wrong > 0:
        st.button("틀린 문제 다시 풀기", key=f"{bkey}_retry", on_click=retry, type="primary")
    if passed and li + 1 < len(levels):
        st.button(f"다음 단계로 ({levels[li + 1]}) ▶", key=f"{bkey}_up", on_click=go, args=(li + 1,))
    if not passed and li > 0:
        st.button(f"이전 단계로 ({levels[li - 1]})", key=f"{bkey}_down", on_click=go, args=(li - 1,))
    st.button("같은 단계 새 문제", key=f"{bkey}_again", on_click=go, args=(li,))


def make_time_q(level: str) -> dict:
    return {"h": random.randint(1, 12), "m": random.choice(LEVELS[level])}


def sol_time(q: dict):
    return (q["h"], q["m"])


def review_clock(q: dict):
    show(draw_clock(q["h"], q["m"], st.session_state.get("show_min", True)))


def ask_read(q, level, kid):
    show(draw_clock(q["h"], q["m"], st.session_state.get("show_min", True)))
    st.write("시계가 가리키는 시각에 맞게 **디지털 시계**를 조정해 보세요 👇")
    c1, c2 = st.columns(2)
    with c1:
        ah = st.number_input("시", 1, 12, 12, key=f"{kid}_h")
    with c2:
        am = st.number_input("분", 0, 59, 0, key=f"{kid}_m")
    big_digital(ah, am)
    return (ah, am)


def explain_read(q, ok, ans):
    head = (
        f"정답이에요! **{read_time(q['h'], q['m'])}** 🎉"
        if ok
        else f"아쉬워요. 정답은 **{read_time(q['h'], q['m'])}**예요."
    )
    body = minute_hint(q["m"])
    if not ok:
        body = wrong_hint(ans[0], ans[1], q["h"], q["m"]) + "\n\n" + body
    return head + "\n\n" + body


def ask_set(q, level, kid):
    st.write("아래 시각이 되도록 **시침과 분침**을 움직여 시계를 맞춰 보세요 👇")
    big_digital(q["h"], q["m"])
    sh = st.slider("🔵 시침(짧은바늘)이 가리키는 시", 1, 12, 12, key=f"{kid}_h")
    sm = st.slider(
        "🔴 분침(긴바늘)이 가리키는 분", 0, 59, 0, step=1 if level == "1분 단위" else 5, key=f"{kid}_m"
    )
    show(draw_clock(sh, sm, st.session_state.get("show_min", True)))
    return (sh, sm)


def explain_set(q, ok, ans):
    if ok:
        return f"시계를 정확히 맞췄어요! **{read_time(q['h'], q['m'])}** 🎉"
    return (
        f"아쉬워요. 내가 맞춘 시각은 {fmt(*ans)}였고, 목표는 **{read_time(q['h'], q['m'])}**예요.\n\n"
        + wrong_hint(ans[0], ans[1], q["h"], q["m"])
        + "\n\n"
        + minute_hint(q["m"])
    )


def make_calc_q(level: str, op_mode: str) -> dict:
    if level == "30분 단위":
        m, delta = random.choice([0, 30]), random.choice([30, 60, 90, 120])
    elif level == "15분 단위":
        m, delta = random.choice([0, 15, 30, 45]), random.choice([15, 30, 45, 60, 75, 90])
    else:
        m, delta = random.choice(range(0, 60, 5)), random.randint(6, 119)
    if op_mode.startswith("더하기"):
        op = 1
    elif op_mode.startswith("빼기"):
        op = -1
    else:
        op = random.choice([1, -1])
    return {"h": random.randint(1, 12), "m": m, "op": op, "delta": delta}


def sol_calc(q: dict):
    return add_time(q["h"], q["m"], q["op"] * q["delta"])


def label_calc(q: dict) -> str:
    sign = "+" if q["op"] > 0 else "−"
    return f"{fmt(q['h'], q['m'])} {sign} {dur_text(q['delta'])}"


def review_calc(q: dict):
    ch, cm = sol_calc(q)
    st.caption("정답 시계")
    show(draw_clock(ch, cm, st.session_state.get("show_min", True)))


def ask_calc(q, level, kid):
    word = "후" if q["op"] > 0 else "전"
    if st.session_state.get("calc_show", "아날로그") == "디지털":
        st.caption("지금 시각")
        big_digital(q["h"], q["m"])
    else:
        st.caption("지금 시각 (시계를 읽어 보세요)")
        show(draw_clock(q["h"], q["m"], st.session_state.get("show_min", True)))
    st.markdown(f"### ⏱ {dur_text(q['delta'])} {word}는 몇 시 몇 분일까요?")
    c1, c2 = st.columns(2)
    with c1:
        ah = st.number_input("시", 1, 12, 12, key=f"{kid}_h")
    with c2:
        am = st.number_input("분", 0, 59, 0, key=f"{kid}_m")
    big_digital(ah, am)
    return (ah, am)


def explain_calc(q, ok, ans):
    ch, cm = sol_calc(q)
    word = "후" if q["op"] > 0 else "전"
    rest = q["delta"] % 60
    parts = ["정답이에요! 🎉" if ok else f"아쉬워요. 내 답은 {fmt(*ans)}였어요."]
    parts.append(f"{read_time(q['h'], q['m'])}에서 {dur_text(q['delta'])} {word} → **{read_time(ch, cm)}**")
    if q["op"] > 0 and q["m"] + rest >= 60:
        parts.append("분을 더했더니 60분이 넘었어요. 60분은 1시간으로 바꿔서 시에 더해요.")
    elif q["op"] < 0 and q["m"] < rest:
        parts.append("분이 모자라요. 1시간을 60분으로 바꿔서 빼요.")
    return "\n\n".join(parts)


def section_explore(show_min: bool):
    S = st.session_state
    for k, v in (("ex_h", 3), ("ex_m", 0), ("ex_hn", 3), ("ex_mn", 0)):
        if k not in S:
            S[k] = v

    def from_slider():
        S["ex_hn"], S["ex_mn"] = S["ex_h"], S["ex_m"]

    def from_digital():
        S["ex_h"], S["ex_m"] = S["ex_hn"], S["ex_mn"]

    def shift(delta):
        h, m = add_time(S["ex_h"], S["ex_m"], delta)
        S["ex_h"], S["ex_m"] = h, m
        S["ex_hn"], S["ex_mn"] = h, m

    st.caption("아날로그 시계와 디지털 시계는 서로 연결되어 있어요. 어느 쪽을 바꿔도 다른 쪽이 함께 바뀝니다.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🕒 아날로그**")
        st.slider("시", 1, 12, key="ex_h", on_change=from_slider)
        st.slider("분", 0, 59, key="ex_m", on_change=from_slider)
    with c2:
        st.markdown("**🔢 디지털**")
        st.number_input("시", 1, 12, key="ex_hn", on_change=from_digital)
        st.number_input("분", 0, 59, key="ex_mn", on_change=from_digital)

    st.caption("빠르게 바꾸기")
    quick = [("−1시간", -60), ("+1시간", 60), ("−10분", -10), ("+10분", 10), ("−1분", -1), ("+1분", 1)]
    cols = st.columns(3)
    for idx, (text, d) in enumerate(quick):
        with cols[idx % 3]:
            st.button(text, key=f"ex_q{idx}", on_click=shift, args=(d,))

    h, m = S["ex_h"], S["ex_m"]
    show(draw_clock(h, m, show_min))
    st.caption("🔵 시침(짧은바늘) = 시 · 🔴 분침(긴바늘) = 분")
    big_digital(h, m)
    ampm = st.radio("오전/오후", ["오전", "오후"], horizontal=True, key="ex_ampm")
    st.success(f"{ampm} **{read_time(h, m)}**")
    st.markdown(minute_hint(m))
    if m == 30:
        st.info("💡 30분은 '반'이라고도 해요. 3시 30분 = 3시 반!")
    h24 = h % 12 + (12 if ampm == "오후" else 0)
    st.caption(f"24시간제로는 {h24:02d}:{m:02d} 이에요.")
    st.info("💡 분침이 한 바퀴(60분) 돌면 시침은 숫자 한 칸(1시간) 움직여요. '+10분' 버튼으로 50분에서 한 번 더 눌러 보세요!")


def section_rewind(show_min: bool):
    st.caption("시간을 앞으로 보내거나(⏩) 뒤로 되돌리면서(⏪) 시침과 분침이 어떻게 함께 움직이는지 살펴봐요.")
    start = st.slider("시작 시각 (정각)", 1, 12, 12, key="rw_start")
    delta = st.slider("지금부터 몇 분? (− 되감기 / + 빨리감기)", -180, 180, 0, step=5, key="rw_delta")
    h, m = add_time(start, 0, delta)
    show(draw_clock(h, m, show_min))
    c1, c2 = st.columns(2)
    with c1:
        st.metric("시작", fmt(start, 0))
    with c2:
        st.metric("지금", fmt(h, m))

    if delta == 0:
        st.info("슬라이더를 움직여 시간을 바꿔 보세요.")
        return
    full, rest = divmod(abs(delta), 60)
    way = "빨리감기 ⏩ 지났어요" if delta > 0 else "되감기 ⏪ 되돌렸어요"
    st.success(f"{dur_text(abs(delta))} {way}")
    st.markdown(f"🔴 분침은 **{full}바퀴**와 **{rest}분** 만큼 돌았어요. (한 바퀴 = 60분)")
    if rest == 0:
        st.markdown(f"🔵 시침은 숫자 **{full}칸** 움직였어요. (1시간 = 숫자 1칸)")
    elif full:
        st.markdown(f"🔵 시침은 숫자 **{full}칸**보다 조금 더 움직였어요. (1시간 = 숫자 1칸)")
    else:
        st.markdown("🔵 시침은 숫자 한 칸보다 조금 덜 움직였어요. (1시간 = 숫자 1칸)")


def section_board():
    hist = st.session_state.get("history") or []
    if not hist:
        st.info("아직 기록이 없어요. 퀴즈를 풀면 여기에 점수가 쌓여요!")
        return
    passed = sum(1 for r in hist if r["통과"] == "✅")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("푼 라운드", len(hist))
    with c2:
        st.metric("통과", passed)
    st.caption("최근 기록이 위에 나와요 (최대 20개).")
    st.table([{k: v for k, v in r.items() if k != "uid"} for r in reversed(hist)][:20])
    st.button("기록 지우기", key="board_clear", on_click=lambda: st.session_state.pop("history", None))


def page_clock():
    st.header("🕒 시계 보기")
    st.checkbox("분 눈금 숫자 보기 (5, 10, 15 …)", value=True, key="show_min")
    section = st.radio("활동 선택", SECTIONS, horizontal=True, key="clock_section", label_visibility="collapsed")
    show_min = st.session_state.get("show_min", True)

    if section == SECTIONS[0]:
        section_explore(show_min)
    elif section == SECTIONS[1]:
        st.caption("시계 그림을 보고 디지털 시계를 같은 시각으로 맞춰 보세요. 정각부터 시작해서 단계가 올라가요.")
        run_quiz("read", "시각 읽기", TIME_LEVELS, make_time_q, ask_read, sol_time, explain_read, review=review_clock)
    elif section == SECTIONS[2]:
        st.caption("목표 시각을 보고 시침과 분침을 직접 움직여 시계를 맞춰 보세요.")
        run_quiz("set", "시계 맞추기", TIME_LEVELS, make_time_q, ask_set, sol_time, explain_set, review=review_clock)
    elif section == SECTIONS[3]:
        section_rewind(show_min)
    elif section == SECTIONS[4]:
        st.caption("먼저 '아날로그'로 연습하고, 익숙해지면 '디지털'로 바꿔 풀어 보세요.")
        st.radio("문제 시계", ["아날로그", "디지털"], horizontal=True, key="calc_show")
        st.radio(
            "계산 종류",
            ["더하기(후)", "빼기(전)", "섞어서"],
            index=2,
            horizontal=True,
            key="calc_op",
            on_change=lambda: st.session_state.pop("calc_st", None),
        )
        run_quiz(
            "calc",
            "시간 계산",
            CALC_LEVELS,
            lambda lv: make_calc_q(lv, st.session_state.get("calc_op", "섞어서")),
            ask_calc,
            sol_calc,
            explain_calc,
            review=review_calc,
            label=label_calc,
        )
    else:
        section_board()


def page_circle():
    st.header("⭕ 원 알아보기")
    tab1, tab2 = st.tabs(["탐구하기", "문제 풀기"])

    with tab1:
        r = st.slider("반지름 (cm)", 1, 10, 5)
        show(draw_circle(r))
        st.caption("🟢 반지름 · 🔴 지름")
        c1, c2, c3 = st.columns(3)
        c1.metric("지름", f"{2 * r} cm")
        c2.metric("원주", f"{2 * r * PI:.2f} cm")
        c3.metric("넓이", f"{r * r * PI:.2f} cm²")
        st.info("💡 원주는 지름의 약 3.14배예요. 이 '약 3.14'를 원주율이라고 해요.")

    with tab2:
        if "cq" not in st.session_state:
            st.session_state.cq = random.randint(2, 9)
        r = st.session_state.cq
        st.write(f"반지름이 **{r} cm**인 원의 **원주**는 몇 cm일까요? (원주율 3.14)")
        ans = st.number_input("정답 입력", min_value=0.0, step=0.01, key="c_ans")
        if st.button("정답 확인", key="c_check"):
            if abs(ans - 2 * r * PI) < 0.01:
                st.success("정답! 🎉")
                st.balloons()
            else:
                st.error("힌트: 원주 = 지름 × 3.14, 지름 = 반지름 × 2")
        if st.button("새 문제", key="c_new"):
            st.session_state.cq = random.randint(2, 9)
            st.rerun()


PAGES = {"🕒 시계 보기": page_clock, "⭕ 원": page_circle}
st.sidebar.title("🧮 재미있는 수학 교실")
choice = st.sidebar.radio("단원 선택", list(PAGES))
PAGES[choice]()
