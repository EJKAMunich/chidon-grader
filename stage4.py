#!/usr/bin/env python3
"""
ЭТАП 4: Подсчёт общих баллов
Вход:  stage1_result.json + stage3_scores.json
Выход: stage4_totals.json (полные результаты + рейтинг)

Запуск:
  python3 stage4.py
"""

import json

def main():
    # Читаем данные
    print("Читаю результаты...")

    with open("stage1_result.json", "r", encoding="utf-8") as f:
        stage1 = json.load(f)

    with open("stage3_scores.json", "r", encoding="utf-8") as f:
        stage3 = json.load(f)

    open_scores = stage3["open_scores"]
    summary = stage1["summary"]

    max_tf = summary["max_tf"]
    max_mc = summary["max_mc"]
    max_open = summary["max_open"]
    max_total = max_tf + max_mc + max_open

    # Считаем итоги по каждому участнику
    results = []

    for p in stage1["participants"]:
        full_name = p["full_name"]

        # Q1-20 из Этапа 1
        tf_total = p["tf_total"]
        mc_total = p["mc_total"]
        auto_total = p["auto_total"]

        # Q21-50 из Этапа 3
        p_open_scores = open_scores.get(full_name, {})
        open_total = sum(s.get("points", 0) for s in p_open_scores.values())

        grand_total = auto_total + open_total

        results.append({
            "name": p["name"],
            "surname": p["surname"],
            "full_name": full_name,
            "language": p["language"],
            "tf_total": tf_total,
            "mc_total": mc_total,
            "auto_total": auto_total,
            "open_total": open_total,
            "grand_total": grand_total,
            "auto_scores": p["auto_scores"],
            "open_scores": p_open_scores,
            "open_answers": p["open_answers"]
        })

    # Сортировка по итогу (от большего к меньшему)
    results.sort(key=lambda x: x["grand_total"], reverse=True)

    # Присваиваем места
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # Печатаем
    print(f"\n{'='*75}")
    print(f"ИТОГОВЫЙ РЕЙТИНГ")
    print(f"{'='*75}")
    print(f"{'#':<4} {'Имя':<30} {'T/F':>5} {'MC':>5} {'Open':>6} {'Итого':>7}")
    print(f"{'-'*75}")

    for r in results:
        print(f"{r['rank']:<4} {r['full_name']:<30} "
              f"{r['tf_total']:>3}/{max_tf:<1} "
              f"{r['mc_total']:>3}/{max_mc:<2} "
              f"{r['open_total']:>4}/{max_open:<3} "
              f"{r['grand_total']:>4}/{max_total}")

    avg = sum(r["grand_total"] for r in results) / len(results)
    print(f"{'-'*75}")
    print(f"Участников: {len(results)} | Средний балл: {avg:.1f}/{max_total}")

    # Сохраняем
    output = {
        "max_scores": {
            "tf": max_tf,
            "mc": max_mc,
            "open": max_open,
            "total": max_total
        },
        "results": results
    }

    output_file = "stage4_totals.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nСохранено: {output_file}")


if __name__ == "__main__":
    main()
