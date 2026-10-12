# Syteca impact → TestRail run

Пишете в Claude Code `/impact AC-12345` → Claude читає поле **Impact_Ekran** у Jira, підбирає кейси в TestRail (P1/P2/P3), показує дублі, застарілі кейси й непокриті сценарії (з чернетками нових кейсів) → після вашого «ок» створює ран і дає посилання.

TestRail: проєкт **AI: CSM2** (project 9, suite 13 "Master").

## Встановлення (один раз, ~10 хв)

1. **Python 3.12+** — https://www.python.org/downloads/windows/ → у першому вікні інсталятора відмітьте **Add python.exe to PATH**.
   Перевірка: `py --version`
2. **VS Code → Extensions (Ctrl+Shift+X) → Claude Code** (Anthropic) → Install → увійдіть у свій акаунт Claude.
3. **Проєкт і бібліотеки** (PowerShell, у папці, де зберігаєте проєкти):
   ```
   git clone https://jira.dev.local/bitbucket/scm/~viktor.kustovskyi/syteca-impact.git
   cd syteca-impact
   py -m pip install -r requirements.txt
   ```
4. **Логіни TestRail і Jira** — зберігаються в Диспетчері облікових даних Windows, не у файлах:
   ```
   py -X utf8 scripts/set_credentials.py testrail
   py -X utf8 scripts/set_credentials.py jira
   ```
5. **Перевірка й перше завантаження кейсів** (~38 000 кейсів, кілька хвилин):
   ```
   py -X utf8 scripts/check_connection.py
   py -X utf8 scripts/sync.py
   ```
   Має вивести `Project 9: AI: CSM2` і `Suite 13: Master`. Далі Claude сам оновлює базу, якщо їй більше доби.

## Використання

1. VS Code → **File → Open Folder** → `syteca-impact` → відкрийте панель Claude Code.
2. Напишіть:
   ```
   /impact https://jira.dev.local/jira/browse/AC-12345
   ```
   Кілька тікетів в один ран зі своєю назвою: `/impact AC-1 AC-2 — один ран, назва "ETR-1 - regression"`
3. Правте звичайними словами: «прибери надлишкові», «об'єднай в один end-to-end кейс», «додай кейс на ...».
4. **«ок»** — лише після цього Claude створює ран / нові кейси в TestRail.

Оновлення проєкту: `git pull` у папці проєкту.

## Правила (`CLAUDE.md`, спільні для команди — змінюйте через pull request)

- Ран будується за полем **Impact_Ekran**, а не за описом бага.
- Без надлишкових кейсів: один кейс — одна перевірка.
- Нові кейси: тільки в наявні папки за змістом, англійською, у стилі сусідніх кейсів, end-to-end, варіанти — в ER.
  Тайтл: `<Area> - <precondition> - <steps> - Check that ...` (до 250 символів).
- Наявні кейси ніколи не редагуються й не видаляються.
- Нічого не створюється в TestRail без вашого явного «ок».

## Що не потрапляє в репозиторій

`data/` (локальна копія кейсів, ~60 MB), `runs/` (ваші списки ранів і чернетки), `.claude/settings.local.json`, логіни/паролі.

## Якщо не працює

| Помилка | Рішення |
|---|---|
| `'py' is not recognized` | Перевстановіть Python з **Add python.exe to PATH** |
| `No module named ...` | `py -m pip install -r requirements.txt` |
| `No credentials ... syteca-testrail` / `HTTP 401` | `py -X utf8 scripts/set_credentials.py testrail` (або `jira`) |
| `CERTIFICATE_VERIFY_FAILED` | Перевірте VPN / корпоративну мережу і що встановлено `truststore` |
| Таймаут / HTTP 500 при створенні кейсів | Повторіть ту саму команду — скрипт знайде вже створені кейси, дублів не буде |
