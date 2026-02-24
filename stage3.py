#!/usr/bin/env python3
"""
ЭТАП 3: AI-проверка открытых вопросов
Вход:  stage2_cards.json
Выход: stage3_scores.json (баллы + переводы + комментарии)

Запуск:
  export ANTHROPIC_API_KEY="sk-ant-..."
  python3 stage3.py
"""

import json
import re
import os
import sys
import time
import unicodedata

# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

API_MODEL = os.environ.get("CHIDON_MODEL", "claude-sonnet-4-5-20250929")
API_PROVIDER = os.environ.get("CHIDON_PROVIDER", "anthropic")
DELAY_BETWEEN_CALLS = 1.5


# ═══════════════════════════════════════════════════════════════
# ПРАВИЛА ОЦЕНКИ
# ═══════════════════════════════════════════════════════════════

RULE_PROMPTS = {
    "STANDARD": """SCORING RULE: Standard
- Correct answer (any language / transliteration): full points
- Wrong or empty: 0""",

    "PROPER_NOUN_STRICT": """SCORING RULE: Strict proper noun
- Exact proper name (any language / transliteration): full points
- ANY description, paraphrase, or explanation instead of the name: STRICTLY 0
- Empty: 0""",

    "WHO_TO_WHOM": """SCORING RULE: Who said to whom (strict direction)
- Both speaker AND receiver correct and clearly indicated: full points
- Only one role correct: half points
- Ambiguous / no roles indicated: 0
- Direction reversed: 0""",

    "TWO_NAMES": """SCORING RULE: Two names required
- Both names correct: full points
- One correct + second blank or plausible: half points
- One correct + second completely wrong: one third points
- Both wrong: 0""",

    "THREE_NAMES": """SCORING RULE: Three names required
- 3 correct: full points
- 2 correct: two thirds points
- 1 correct: one third points
- 0 correct: 0""",
}


# ═══════════════════════════════════════════════════════════════
# ПОСТРОЕНИЕ ПРОМПТА
# ═══════════════════════════════════════════════════════════════

def build_prompt(card):
    """Строит промпт. AI возвращает баллы + перевод ответа на английский."""
    q_num = card["question_number"]
    q_text = card["question_text"]
    correct = card["correct_answer"]
    max_pts = card["points"]
    rule = card["rule"]

    rule_type = rule["type"]
    rule_text = RULE_PROMPTS.get(rule_type, RULE_PROMPTS["STANDARD"])

    extras = []
    if rule["traps"]:
        extras.append(f"TRAPS (always = 0 points): {', '.join(rule['traps'])}")
    if rule["alt_answers"]:
        extras.append(f"ALTERNATIVE CORRECT ANSWERS (full points): {', '.join(rule['alt_answers'])}")
    if rule["speaker"]:
        extras.append(f"Speaker: {rule['speaker']}")
        extras.append(f"Receiver: {rule['receiver']}")
    if rule["strict_name"]:
        extras.append("STRICT: Only exact proper nouns accepted. Descriptions = 0.")
    if rule["partial_scores"]:
        parts = [f"{k} correct → {v} pts" for k, v in sorted(rule["partial_scores"].items(), reverse=True)]
        extras.append(f"PARTIAL SCORING: {', '.join(parts)}")

    extras_text = "\n".join(extras) if extras else ""

    answer_lines = []
    for i, p in enumerate(card["participants"]):
        answer_lines.append(f"{i+1}. {p['name']} ({p['language']}): {p['answer']}")

    possible = sorted(set([0, max_pts // 3, max_pts // 2, max_pts]))
    possible_str = ", ".join(str(p) for p in possible)

    prompt = f"""Grade question Q{q_num}. Reply ONLY with a CSV table, no other text.

QUESTION Q{q_num}: {q_text}
CORRECT ANSWER: {correct}
MAX POINTS: {max_pts}

{rule_text}

{extras_text}

IMPORTANT:
- Accept answers in ANY language (Russian, Bulgarian, Hebrew, Italian, German, Czech, Hungarian, Spanish, English, etc.)
- Accept any reasonable transliteration of proper nouns
- Possible point values: {possible_str}

TRANSLATION RULE:
- In the "Translation" column, provide the English translation of the participant's answer.
- If the answer is already in English or German, write "—" (dash).
- If the answer is empty, write "—".
- The translation should be literal (what they wrote), NOT what the correct answer is.

PARTICIPANT ANSWERS:
{chr(10).join(answer_lines)}

Reply ONLY with this CSV (semicolon delimiter):
Nr;Name;Points;Translation;Comment
1;{card['participants'][0]['name']};[points];[English translation or —];[brief comment]
..."""

    return prompt


# ═══════════════════════════════════════════════════════════════
# ПАРСИНГ ОТВЕТА
# ═══════════════════════════════════════════════════════════════

def norm(s):
    return unicodedata.normalize("NFC", s.lower().strip())


def match_participant_name(response_name, participant_names):
    response_clean = norm(response_name)
    for pname in participant_names:
        if response_clean == norm(pname):
            return pname
    for pname in participant_names:
        parts = norm(pname).split()
        if any(p in response_clean for p in parts if len(p) >= 3):
            return pname
    for pname in participant_names:
        first = norm(pname).split()[0]
        if len(first) >= 4 and first in response_clean:
            return pname
    return None


def parse_response(text, participant_names):
    """Парсит CSV с 5 колонками: Nr;Name;Points;Translation;Comment"""
    results = {}

    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("Nr") or line.startswith("---"):
            continue

        parts = line.split(";")
        if len(parts) < 4:
            parts = re.split(r'[;|]', line)
        if len(parts) < 4:
            continue

        try:
            nr = parts[0].strip()
            if not nr.isdigit():
                continue

            name = parts[1].strip()
            pts_match = re.search(r'(\d+)', parts[2].strip())
            points = int(pts_match.group(1)) if pts_match else 0
            translation = parts[3].strip() if len(parts) > 3 else "—"
            comment = parts[4].strip() if len(parts) > 4 else ""

            # Очистка translation
            if translation.lower() in ("", "-", "—", "n/a", "none"):
                translation = "—"

            matched = match_participant_name(name, participant_names)
            if matched:
                results[matched] = {
                    "points": points,
                    "translation": translation,
                    "comment": comment,
                    "method": "llm"
                }
        except (ValueError, IndexError):
            continue

    return results


# ═══════════════════════════════════════════════════════════════
# ВЫЗОВ API
# ═══════════════════════════════════════════════════════════════

def call_api(prompt, api_key):
    from llm_client import call_llm
    return call_llm(
        prompt,
        provider=API_PROVIDER,
        model=API_MODEL,
        api_key=api_key,
    )


# ═══════════════════════════════════════════════════════════════
# ОСНОВНОЙ ПРОЦЕСС
# ═══════════════════════════════════════════════════════════════

def grade_all_cards(cards, api_key):
    all_scores = {}
    raw_responses = {}
    total = len(cards)

    for idx, (q_num_str, card) in enumerate(sorted(cards.items(), key=lambda x: int(x[0]))):
        q_num = int(q_num_str)
        n_answers = len(card["participants"])
        participant_names = [p["name"] for p in card["participants"]]

        print(f"  Q{q_num}: {n_answers} ответов ({idx+1}/{total})...", end=" ", flush=True)

        prompt = build_prompt(card)

        try:
            response_text = call_api(prompt, api_key)
            raw_responses[q_num_str] = response_text

            results = parse_response(response_text, participant_names)
            matched = len(results)

            for pname, score_data in results.items():
                if pname not in all_scores:
                    all_scores[pname] = {}
                all_scores[pname][q_num] = score_data

            unmatched = set(participant_names) - set(results.keys())
            if unmatched:
                print(f"✓ ({matched}/{n_answers}) ⚠ пропущены: {len(unmatched)}")
            else:
                print(f"✓ ({matched}/{n_answers})")

        except Exception as e:
            print(f"✗ ОШИБКА: {e}")
            raw_responses[q_num_str] = f"ERROR: {e}"

        time.sleep(DELAY_BETWEEN_CALLS)

    return all_scores, raw_responses


# ═══════════════════════════════════════════════════════════════
# СОХРАНЕНИЕ
# ═══════════════════════════════════════════════════════════════

def save_scores(all_scores, auto_zeros, raw_responses, filepath):
    combined = {}

    for name, zeros in auto_zeros.items():
        if name not in combined:
            combined[name] = {}
        for q_num, score_data in zeros.items():
            combined[name][str(q_num)] = score_data

    for name, scores in all_scores.items():
        if name not in combined:
            combined[name] = {}
        for q_num, score_data in scores.items():
            combined[name][str(q_num)] = score_data

    output = {
        "open_scores": combined,
        "raw_responses": raw_responses
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_summary(all_scores, auto_zeros):
    total_llm = sum(len(s) for s in all_scores.values())
    total_auto = sum(len(z) for z in auto_zeros.values())

    print(f"\n{'='*60}")
    print(f"ЭТАП 3: Результаты AI-проверки")
    print(f"{'='*60}")
    print(f"Проверено через AI:  {total_llm}")
    print(f"Автоматических нулей: {total_auto}")
    print(f"Всего оценок:        {total_llm + total_auto}")


# ═══════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════

def main():
    input_file = "stage2_cards.json"
    output_file = "stage3_scores.json"

    api_key = os.environ.get("CHIDON_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    if not api_key:
        print("ОШИБКА: Не задан API-ключ!")
        print('  export CHIDON_API_KEY="your-key"')
        sys.exit(1)

    print(f"Провайдер: {API_PROVIDER}, Модель: {API_MODEL}")

    print("Читаю карточки из Этапа 2...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = data["cards"]
    auto_zeros = data["auto_zeros"]
    stats = data["stats"]

    print(f"  Вопросов для AI: {len(cards)}")
    print(f"  Ответов для AI:  {stats['needs_llm']}")
    print(f"  Автонулей:       {stats['auto_zero']}")

    print(f"\nОтправка запросов в {API_PROVIDER} API...")
    all_scores, raw_responses = grade_all_cards(cards, api_key)

    print_summary(all_scores, auto_zeros)
    save_scores(all_scores, auto_zeros, raw_responses, output_file)
    print(f"\nСохранено: {output_file}")


if __name__ == "__main__":
    main()
