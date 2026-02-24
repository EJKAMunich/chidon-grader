"""
i18n.py - Internationalization for Chidon HaTanach Grader
Languages: English, Deutsch, Russian
"""

STRINGS = {
    # Navigation
    "nav_home": {"en": "Home", "de": "Startseite", "ru": "Главная"},
    "nav_grader": {"en": "Grader", "de": "Bewertung", "ru": "Проверка"},
    "nav_converter": {"en": "File Converter", "de": "Datei-Konverter", "ru": "Конвертер"},

    # Sidebar
    "sidebar_title": {"en": "Chidon HaTanach", "de": "Chidon HaTanach", "ru": "Хидон ХаТанах"},
    "sidebar_api_key": {"en": "API Key", "de": "API-Schluessel", "ru": "API-ключ"},
    "sidebar_provider": {"en": "AI Provider", "de": "KI-Anbieter", "ru": "AI-провайдер"},
    "sidebar_model": {"en": "Model", "de": "Modell", "ru": "Модель"},
    "sidebar_custom_model": {"en": "Or custom model string:", "de": "Oder eigener Modell-String:", "ru": "Или свой ID модели:"},
    "sidebar_language": {"en": "Language", "de": "Sprache", "ru": "Язык"},
    "sidebar_staged": {"en": "Staged for Grader:", "de": "Bereit:", "ru": "Подготовлено:"},
    "sidebar_key_ready": {"en": "Answer Key", "de": "Antwortschluessel", "ru": "Ключ ответов"},
    "sidebar_ans_ready": {"en": "Participant Answers", "de": "Teilnehmerantworten", "ru": "Ответы участников"},

    # Home page
    "home_title": {"en": "Chidon HaTanach Grader", "de": "Chidon HaTanach Bewertungssystem", "ru": "Система оценки Хидон ХаТанах"},
    "home_subtitle": {
        "en": "Automated grading system for Bible knowledge competitions",
        "de": "Automatisches Bewertungssystem fuer Bibelwissens-Wettbewerbe",
        "ru": "Автоматическая система проверки олимпиад по знанию Танаха",
    },
    "home_what_title": {"en": "What is this?", "de": "Was ist das?", "ru": "Что это?"},
    "home_what_text": {
        "en": "This app automatically grades multilingual Bible knowledge competitions (Chidon HaTanach). "
              "It handles True/False, multiple choice, and open-ended questions across any number of languages. "
              "Open questions are graded by AI, which understands answers in all languages and awards partial credit.",
        "de": "Diese App bewertet automatisch mehrsprachige Bibelwissens-Wettbewerbe (Chidon HaTanach). "
              "Sie verarbeitet Richtig/Falsch-, Multiple-Choice- und offene Fragen in beliebig vielen Sprachen. "
              "Offene Fragen werden von KI bewertet, die Antworten in allen Sprachen versteht und Teilpunkte vergibt.",
        "ru": "Приложение автоматически проверяет многоязычные олимпиады по Танаху (Хидон ХаТанах). "
              "Поддерживаются вопросы Верно/Неверно, множественный выбор и открытые вопросы на любом количестве языков. "
              "Открытые вопросы проверяет AI, который понимает ответы на всех языках и выставляет частичные баллы.",
    },
    "home_how_title": {"en": "How to use", "de": "So funktioniert es", "ru": "Как пользоваться"},
    "home_step1_title": {"en": "Option A: Direct Grading", "de": "Option A: Direkte Bewertung", "ru": "Вариант А: Прямая проверка"},
    "home_step1_text": {
        "en": "If your files are already in the correct format, go to Grader, upload them, and click Run.",
        "de": "Wenn Ihre Dateien bereits im richtigen Format sind, gehen Sie zu Bewertung, laden Sie sie hoch und klicken Sie auf Start.",
        "ru": "Если файлы уже в нужном формате, перейдите в Проверку, загрузите их и нажмите Запуск.",
    },
    "home_step2_title": {"en": "Option B: Convert then Grade", "de": "Option B: Konvertieren, dann Bewerten", "ru": "Вариант Б: Конвертация, затем проверка"},
    "home_step2_text": {
        "en": "Have raw files from Google Forms, PDF, or any format? Go to File Converter first. "
              "AI will extract and structure the data. Review, edit if needed, then send to Grader.",
        "de": "Haben Sie Rohdaten von Google Forms, PDF oder anderem Format? Gehen Sie zuerst zum Datei-Konverter. "
              "KI extrahiert und strukturiert die Daten. Pruefen, ggf. bearbeiten, dann zur Bewertung senden.",
        "ru": "Есть необработанные файлы из Google Forms, PDF или другого формата? Начните с Конвертера. "
              "AI извлечет и структурирует данные. Проверьте, отредактируйте при необходимости, затем отправьте на проверку.",
    },
    "home_formats_title": {"en": "File Formats", "de": "Dateiformate", "ru": "Форматы файлов"},
    "home_key_format_title": {"en": "Answer Key", "de": "Antwortschluessel", "ru": "Ключ ответов"},
    "home_key_format_text": {
        "en": "Excel file with columns: Number, Question, Answer, Points, Comment.\n\n"
              "T/F answers: write T or F. "
              "Multiple choice: write A, B, C, or D. "
              "Open questions: write the expected answer. "
              "Comment: optional notes (e.g. alternative answers).",
        "de": "Excel-Datei mit Spalten: Number, Question, Answer, Points, Comment.\n\n"
              "R/F-Antworten: T oder F. "
              "Multiple Choice: A, B, C oder D. "
              "Offene Fragen: die erwartete Antwort. "
              "Comment: optionale Hinweise (z.B. alternative Antworten).",
        "ru": "Excel-файл со столбцами: Number, Question, Answer, Points, Comment.\n\n"
              "Верно/Неверно: пишите T или F. "
              "Множественный выбор: пишите A, B, C или D. "
              "Открытые вопросы: напишите ожидаемый ответ. "
              "Comment: необязательные пометки (например, альтернативные ответы).",
    },
    "home_ans_format_title": {"en": "Participant Answers", "de": "Teilnehmerantworten", "ru": "Ответы участников"},
    "home_ans_format_text": {
        "en": "Excel file with columns: Name, Surname, Language, Q1, Q2, ... Q50.\n\n"
              "Language: the language each participant wrote in (e.g. English, Deutsch). "
              "T/F answers: T or F only. "
              "Multiple choice: the letter only (A, B, C, or D, no text). "
              "Open answers: the participant's text as-is.\n\n"
              "Or use File Converter to parse any format automatically.",
        "de": "Excel-Datei mit Spalten: Name, Surname, Language, Q1, Q2, ... Q50.\n\n"
              "Language: Sprache des Teilnehmers (z.B. English, Deutsch). "
              "R/F-Antworten: nur T oder F. "
              "Multiple Choice: nur der Buchstabe (A, B, C oder D, kein Text). "
              "Offene Antworten: der Text des Teilnehmers.\n\n"
              "Oder nutzen Sie den Datei-Konverter.",
        "ru": "Excel-файл со столбцами: Name, Surname, Language, Q1, Q2, ... Q50.\n\n"
              "Language: язык, на котором писал участник (например, English, Deutsch). "
              "Верно/Неверно: только T или F. "
              "Множественный выбор: только буква (A, B, C или D, без текста). "
              "Открытые ответы: текст участника как есть.\n\n"
              "Или используйте Конвертер.",
    },
    "home_download_template": {"en": "Download Answer Key Template", "de": "Vorlage herunterladen", "ru": "Скачать шаблон ключа"},
    # Grader page
    "grader_title": {"en": "Grader", "de": "Bewertung", "ru": "Проверка"},
    "grader_from_converter": {"en": "Files loaded from File Converter", "de": "Dateien aus Konverter geladen", "ru": "Файлы загружены из конвертера"},
    "grader_clear": {"en": "Clear and upload manually", "de": "Loeschen und manuell hochladen", "ru": "Очистить и загрузить вручную"},
    "grader_upload_hint": {"en": "Upload template files or use File Converter to prepare them.", "de": "Laden Sie Vorlagen-Dateien hoch oder nutzen Sie den Konverter.", "ru": "Загрузите файлы-шаблоны или подготовьте через конвертер."},
    "grader_key_label": {"en": "Answer Key", "de": "Antwortschluessel", "ru": "Ключ ответов"},
    "grader_ans_label": {"en": "Participant Answers", "de": "Teilnehmerantworten", "ru": "Ответы участников"},
    "grader_upload_both": {"en": "Upload both files to continue, or use File Converter to prepare raw files.", "de": "Laden Sie beide Dateien hoch, oder nutzen Sie den Datei-Konverter.", "ru": "Загрузите оба файла или воспользуйтесь Конвертером."},
    "grader_preview": {"en": "Data Preview", "de": "Datenvorschau", "ru": "Предпросмотр"},
    "grader_no_key": {"en": "Enter your API key in the sidebar.", "de": "Geben Sie Ihren API-Schluessel in der Seitenleiste ein.", "ru": "Введите API-ключ в боковой панели."},
    "grader_run": {"en": "Run Grader", "de": "Bewertung starten", "ru": "Запустить проверку"},
    "grader_timeout": {"en": "Pipeline timed out", "de": "Zeitueberschreitung", "ru": "Превышено время ожидания"},
    "grader_failed": {"en": "Pipeline failed.", "de": "Bewertung fehlgeschlagen.", "ru": "Проверка завершилась с ошибкой."},
    "grader_results": {"en": "Results", "de": "Ergebnisse", "ru": "Результаты"},
    "grader_exec_log": {"en": "Execution Log", "de": "Ausfuehrungsprotokoll", "ru": "Журнал выполнения"},

    # Converter page
    "conv_title": {"en": "File Converter", "de": "Datei-Konverter", "ru": "Конвертер файлов"},
    "conv_desc": {
        "en": "Convert any file into the template format. Supported: Excel, CSV, PDF, Word, plain text. "
              "AI extracts and structures the data. You review and edit, then download or send to Grader.",
        "de": "Konvertieren Sie jede Datei ins Vorlagen-Format. Unterstuetzt: Excel, CSV, PDF, Word, Text. "
              "KI extrahiert und strukturiert die Daten. Sie pruefen und bearbeiten, dann herunterladen oder zur Bewertung senden.",
        "ru": "Конвертируйте файл любого формата. Поддерживаются: Excel, CSV, PDF, Word, текст. "
              "AI извлечет и структурирует данные. Проверьте, отредактируйте и отправьте на проверку.",
    },
    "conv_tab_key": {"en": "Answer Key", "de": "Antwortschluessel", "ru": "Ключ ответов"},
    "conv_tab_ans": {"en": "Participant Answers", "de": "Teilnehmerantworten", "ru": "Ответы участников"},
    "conv_upload": {"en": "Upload file", "de": "Datei hochladen", "ru": "Загрузить файл"},
    "conv_upload_help": {"en": "Excel, CSV, PDF, Word, or text file", "de": "Excel, CSV, PDF, Word oder Text", "ru": "Excel, CSV, PDF, Word или текст"},
    "conv_analyze": {"en": "Analyze", "de": "Analysieren", "ru": "Анализировать"},
    "conv_already_parsed": {"en": "already parsed", "de": "bereits geparst", "ru": "уже обработан"},
    "conv_edit_hint": {"en": "Review and edit the parsed data. Changes are saved automatically.", "de": "Pruefen und bearbeiten Sie die Daten. Aenderungen werden automatisch gespeichert.", "ru": "Проверьте и отредактируйте данные. Изменения сохраняются автоматически."},
    "conv_download": {"en": "Download", "de": "Herunterladen", "ru": "Скачать"},
    "conv_stage": {"en": "Stage for Grader", "de": "Zur Bewertung", "ru": "В проверку"},
    "conv_clear": {"en": "Clear", "de": "Loeschen", "ru": "Очистить"},
    "conv_staged_ok": {"en": "staged for Grader!", "de": "fuer Bewertung bereit!", "ru": "подготовлено для проверки!"},
    "conv_send_title": {"en": "Send to Grader", "de": "Zur Bewertung senden", "ru": "Отправить на проверку"},
    "conv_go_grader": {"en": "Go to Grader", "de": "Zur Bewertung", "ru": "Перейти к проверке"},
    "conv_key_ready": {"en": "ready", "de": "bereit", "ru": "готово"},
    "conv_not_staged": {"en": "not staged yet", "de": "noch nicht bereit", "ru": "еще не готово"},
    "conv_stage_both": {"en": "Parse and stage both files above to enable grading.", "de": "Parsen und vorbereiten Sie beide Dateien.", "ru": "Обработайте и подготовьте оба файла."},
    "conv_mismatch_key": {
        "en": "This file has many columns with long headers. It looks like Participant Answers, not an Answer Key. Wrong tab?",
        "de": "Diese Datei hat viele Spalten mit langen Ueberschriften. Sieht aus wie Teilnehmerantworten, nicht ein Antwortschluessel. Falscher Tab?",
        "ru": "В файле много столбцов с длинными заголовками. Похоже на ответы участников, а не ключ. Не тот таб?",
    },
    "conv_mismatch_ans": {
        "en": "This file looks like an Answer Key, not Participant Answers. Wrong tab?",
        "de": "Diese Datei sieht aus wie ein Antwortschluessel, nicht Teilnehmerantworten. Falscher Tab?",
        "ru": "Файл похож на ключ ответов, а не ответы участников. Не тот таб?",
    },

    # Shared
    "questions": {"en": "Questions", "de": "Fragen", "ru": "Вопросов"},
    "max_score": {"en": "Max Score", "de": "Max. Punkte", "ru": "Макс. баллы"},
    "participants": {"en": "Participants", "de": "Teilnehmer", "ru": "Участников"},
    "true_false": {"en": "True/False", "de": "Richtig/Falsch", "ru": "Верно/Неверно"},
    "multiple_choice": {"en": "Multiple Choice", "de": "Multiple Choice", "ru": "Мн. выбор"},
    "open": {"en": "Open", "de": "Offen", "ru": "Открытые"},
    "languages": {"en": "Languages", "de": "Sprachen", "ru": "Языки"},
    "special_rules": {"en": "Special rules (comments)", "de": "Sonderregeln (Kommentare)", "ru": "Спец. правила (комментарии)"},
    "ranking": {"en": "Ranking", "de": "Rangliste", "ru": "Рейтинг"},
    "max_possible": {"en": "Max possible", "de": "Maximum", "ru": "Максимум"},
    "highest": {"en": "Highest", "de": "Hoechste", "ru": "Лучший"},
    "average": {"en": "Average", "de": "Durchschnitt", "ru": "Средний"},
    "lowest": {"en": "Lowest", "de": "Niedrigste", "ru": "Худший"},
    "download": {"en": "Download", "de": "Herunterladen", "ru": "Скачать"},
    "fix_errors": {"en": "Fix errors before proceeding.", "de": "Fehler beheben.", "ru": "Исправьте ошибки."},
    "parsing_failed": {"en": "Parsing failed. Fix your source file and try again.", "de": "Parsen fehlgeschlagen. Quelldatei korrigieren.", "ru": "Парсинг не удался. Исправьте исходный файл."},
    "ai_mapping": {"en": "AI column mapping", "de": "KI-Spaltenzuordnung", "ru": "AI-маппинг столбцов"},
}


def t(key, lang="en"):
    """Get translated string."""
    entry = STRINGS.get(key, {})
    return entry.get(lang, entry.get("en", f"[{key}]"))
