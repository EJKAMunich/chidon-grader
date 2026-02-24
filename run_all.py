#!/usr/bin/env python3
"""
🏆 CHIDON TANACH — Мастер-скрипт
Запускает все этапы последовательно.

Вход:  Key.xlsx + Answers.xlsx (в текущей папке)
Выход: ranking.docx + report_cards.docx

Перед запуском:
  pip3 install openpyxl anthropic python-docx
  export ANTHROPIC_API_KEY="sk-ant-..."

Запуск:
  python3 run_all.py
"""

import subprocess
import sys
import os

def run_stage(script, description):
    """Запускает скрипт и проверяет результат."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")

    result = subprocess.run([sys.executable, script], capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ ОШИБКА в {script}! Процесс остановлен.")
        sys.exit(1)

    print(f"✅ {description} — завершён")


def main():
    # Проверка файлов
    for f in ["Key.xlsx", "Answers.xlsx"]:
        if not os.path.exists(f):
            print(f"ОШИБКА: Файл {f} не найден в текущей папке!")
            sys.exit(1)

    # Проверка API-ключа
    if not os.environ.get("CHIDON_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ОШИБКА: Не задан API-ключ!")
        print('Выполни:  export CHIDON_API_KEY="your-key"')
        print('  или:    export ANTHROPIC_API_KEY="sk-ant-..."')
        sys.exit(1)

    # Проверка скриптов
    for f in ["stage1.py", "stage2.py", "stage3.py", "stage4.py", "stage5.py"]:
        if not os.path.exists(f):
            print(f"ОШИБКА: Скрипт {f} не найден!")
            sys.exit(1)

    print("🏆 CHIDON TANACH — Полная проверка")
    print(f"  Ключ:   Key.xlsx")
    print(f"  Ответы: Answers.xlsx")

    run_stage("stage1.py", "Этап 1: Автоподсчёт T/F и MC")
    run_stage("stage2.py", "Этап 2: Подготовка карточек для AI")
    run_stage("stage3.py", "Этап 3: AI-проверка открытых вопросов")
    run_stage("stage4.py", "Этап 4: Подсчёт общих баллов")
    run_stage("stage5.py", "Этап 5: Генерация Word-документов")

    print(f"\n{'='*60}")
    print(f"🏆 ВСЁ ГОТОВО!")
    print(f"{'='*60}")
    print(f"  📊 Рейтинг:  ranking.docx")
    print(f"  📋 Карточки:  report_cards.docx")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
