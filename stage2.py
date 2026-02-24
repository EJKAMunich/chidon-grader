#!/usr/bin/env python3
"""
ЭТАП 2: Подготовка карточек для AI
Вход:  stage1_result.json
Выход: stage2_cards.json (карточки вопросов для AI-проверки)
       + автоматические нули для пустых ответов

Запуск:
  python3 stage2.py
"""

import json
import re

# ═══════════════════════════════════════════════════════════════
# ШАГ 1: Парсинг комментариев ключа в правила
# ═══════════════════════════════════════════════════════════════

def parse_comment(answer, comment):
    """
    Парсит свободный комментарий из ключа в структурированное правило.

    Распознаёт нотацию:
      Trap: X=0             → ловушка (ответ X = 0 баллов)
      Alt: X                → альтернативный правильный ответ
      Strict: Speaker->Receiver → правило "кто кому"
      Score: 2->6, 1->3    → частичные баллы (N правильных → M баллов)
      Exact name only       → описания = 0 баллов
    """
    rule = {
        "type": "STANDARD",       # тип правила
        "traps": [],              # ловушки
        "alt_answers": [],        # альтернативные правильные ответы
        "partial_scores": {},     # частичные баллы {кол-во: баллы}
        "speaker": "",            # для WHO_TO_WHOM
        "receiver": "",           # для WHO_TO_WHOM
        "strict_name": False,     # описания = 0
    }

    if not comment:
        # Определяем тип по формату ответа
        rule["type"] = detect_type_from_answer(answer)
        return rule

    comment_lower = comment.lower()

    # Trap: X=0
    trap_matches = re.findall(r'trap:\s*([^=]+)=\s*0', comment, re.IGNORECASE)
    for trap in trap_matches:
        rule["traps"].append(trap.strip())

    # Alt: X
    alt_matches = re.findall(r'alt:\s*(.+?)(?:\.|$)', comment, re.IGNORECASE)
    for alt in alt_matches:
        rule["alt_answers"].append(alt.strip())

    # Strict: Speaker->Receiver
    strict_match = re.search(r'strict:\s*speaker\s*->\s*receiver', comment, re.IGNORECASE)
    if strict_match:
        rule["type"] = "WHO_TO_WHOM"
        # Извлекаем имена из основного ответа (формат "X to Y")
        parts = re.split(r'\s+to\s+', answer, flags=re.IGNORECASE)
        if len(parts) == 2:
            rule["speaker"] = parts[0].strip()
            rule["receiver"] = parts[1].strip()

    # Score: 2->6, 1->3
    score_matches = re.findall(r'(\d+)\s*->\s*(\d+)', comment)
    if score_matches and not strict_match:
        for count, points in score_matches:
            rule["partial_scores"][int(count)] = int(points)
        # Определяем тип по количеству ожидаемых имён
        max_count = max(int(c) for c, _ in score_matches)
        if max_count == 2:
            rule["type"] = "TWO_NAMES"
        elif max_count == 3:
            rule["type"] = "THREE_NAMES"

    # Exact name only
    if "exact name only" in comment_lower:
        rule["strict_name"] = True
        if rule["type"] == "STANDARD":
            rule["type"] = "PROPER_NOUN_STRICT"

    # Если тип не определился из комментария — определяем из ответа
    if rule["type"] == "STANDARD":
        rule["type"] = detect_type_from_answer(answer)

    return rule


def detect_type_from_answer(answer):
    """
    Определяет тип правила по формату ответа.
    """
    # "X to Y" → WHO_TO_WHOM
    if re.search(r'\s+to\s+', answer, re.IGNORECASE):
        return "WHO_TO_WHOM"

    # "X and Y" или "X, Y" (два имени) → TWO_NAMES
    if re.search(r'\s+and\s+', answer, re.IGNORECASE) or ',' in answer:
        parts = re.split(r'\s+and\s+|,', answer)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) == 2:
            return "TWO_NAMES"
        elif len(parts) >= 3:
            return "THREE_NAMES"

    return "STANDARD"


# ═══════════════════════════════════════════════════════════════
# ШАГ 2: Классификация ответов
# ═══════════════════════════════════════════════════════════════

def classify_answers(data):
    """
    Классифицирует каждый ответ на открытый вопрос:
      - "auto_zero": пустой ответ → 0 баллов, AI не нужен
      - "needs_llm": непустой ответ → нужна проверка AI

    Возвращает:
      - cards: словарь {q_num: {question_info + participants_to_check}}
      - auto_zeros: словарь {participant_name: {q_num: 0}}
      - stats: статистика классификации
    """
    open_key = data["open_key"]
    participants = data["participants"]

    cards = {}       # Карточки для AI
    auto_zeros = {}  # Автоматические нули
    stats = {"total_pairs": 0, "auto_zero": 0, "needs_llm": 0}

    for q_num_str, q_info in open_key.items():
        q_num = int(q_num_str)

        # Парсим правило из комментария
        rule = parse_comment(q_info["answer"], q_info["comment"])

        # Собираем ответы участников
        to_check = []

        for p in participants:
            full_name = p["full_name"]
            answer = p["open_answers"].get(q_num_str, "")
            stats["total_pairs"] += 1

            if not answer.strip():
                # Пустой ответ — автоматический 0
                if full_name not in auto_zeros:
                    auto_zeros[full_name] = {}
                auto_zeros[full_name][q_num] = {
                    "points": 0,
                    "comment": "Empty",
                    "method": "auto"
                }
                stats["auto_zero"] += 1
            else:
                # Непустой — нужен AI
                to_check.append({
                    "name": full_name,
                    "language": p["language"],
                    "answer": answer
                })
                stats["needs_llm"] += 1

        # Создаём карточку только если есть что проверять
        if to_check:
            cards[q_num] = {
                "question_number": q_num,
                "question_text": q_info["text"],
                "correct_answer": q_info["answer"],
                "points": q_info["points"],
                "comment": q_info["comment"],
                "rule": rule,
                "participants": to_check
            }

    return cards, auto_zeros, stats


# ═══════════════════════════════════════════════════════════════
# ШАГ 3: Формирование карточек и сохранение
# ═══════════════════════════════════════════════════════════════

def save_cards(cards, auto_zeros, stats, data, filepath):
    """Сохраняет карточки и автонули в JSON."""
    output = {
        "stats": stats,
        "auto_zeros": auto_zeros,
        "cards": {}
    }

    for q_num, card in cards.items():
        output["cards"][str(q_num)] = card

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_summary(cards, auto_zeros, stats):
    """Печатает сводку классификации."""
    print(f"\n{'='*60}")
    print(f"ЭТАП 2: Классификация ответов")
    print(f"{'='*60}")
    print(f"Всего пар (участник × вопрос):  {stats['total_pairs']}")
    print(f"  Автоматический 0 (пустые):    {stats['auto_zero']}")
    print(f"  Нужна проверка AI:            {stats['needs_llm']}")
    saved = (1 - stats['needs_llm'] / max(stats['total_pairs'], 1)) * 100
    print(f"  Экономия:                     {saved:.0f}% без AI")

    print(f"\nКарточки для AI: {len(cards)} вопросов")
    print(f"{'Q#':<5} {'Тип':<20} {'Ответов':>8} {'Правило':>15}")
    print(f"{'-'*55}")
    for q_num in sorted(cards.keys()):
        card = cards[q_num]
        rule_type = card["rule"]["type"]
        n_answers = len(card["participants"])
        traps = f" ⚠{len(card['rule']['traps'])}" if card["rule"]["traps"] else ""
        print(f"Q{q_num:<4} {card['question_text'][:18]:<20} {n_answers:>5}"
              f"    {rule_type}{traps}")


# ═══════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════

def main():
    input_file = "stage1_result.json"
    output_file = "stage2_cards.json"

    print("Читаю результаты Этапа 1...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"  Участников: {data['summary']['total_participants']}")
    print(f"  Открытых вопросов: {data['summary']['open_questions']}")

    print("Классифицирую ответы...")
    cards, auto_zeros, stats = classify_answers(data)

    print_summary(cards, auto_zeros, stats)
    save_cards(cards, auto_zeros, stats, data, output_file)
    print(f"\nСохранено: {output_file}")


if __name__ == "__main__":
    main()
