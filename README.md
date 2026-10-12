# Syteca impact → TestRail run

Подбирает тест-кейсы TestRail под импакт задачи из Jira (поле **Impact_Ekran**) и создаёт тест-ран.
Работает через Claude Code в VS Code: вы пишете `/impact AC-12345`, Claude находит кейсы, предлагает тиры P1/P2/P3,
непокрытые сценарии (и новые кейсы для них), а после вашего «ок» создаёт ран в TestRail.

Проект TestRail: **AI: CSM2** (project 9, suite 13 "Master").

## Установка (один раз)

1. **Python 3.12+**
   - Скачайте установщик с https://www.python.org/downloads/windows/ и запустите.
   - В первом окне отметьте **"Add python.exe to PATH"** → **Install Now**.
   - Проверка: откройте PowerShell и выполните `py --version` — должно вывести `Python 3.12.x` или новее.

2. **VS Code + Claude Code**
   - В VS Code: слева иконка **Extensions** (Ctrl+Shift+X) → найдите **Claude Code** (издатель Anthropic) → **Install**.
   - Войдите в свой аккаунт Claude, когда расширение попросит.

3. **Скачать проект**
   - В PowerShell перейдите в папку, где храните проекты, и выполните:
     ```
     git clone <ссылка на репозиторий в Bitbucket>
     cd syteca-impact
     ```

4. **Библиотеки Python** (в папке проекта):
   ```
   py -m pip install -r requirements.txt
   ```

5. **Ваши логины к TestRail и Jira**
   Логин и пароль сохраняются в Диспетчер учётных данных Windows — в файлы проекта они не попадают.
   ```
   py -X utf8 scripts/set_credentials.py testrail
   py -X utf8 scripts/set_credentials.py jira
   ```
   Введите логин и пароль (пароль при вводе не отображается — это нормально).

6. **Проверка подключения**
   ```
   py -X utf8 scripts/check_connection.py
   ```
   Должно вывести `Project 9: AI: CSM2` и `Suite 13: Master`.

7. **Первая загрузка кейсов** (несколько минут, ~38 000 кейсов)
   ```
   py -X utf8 scripts/sync.py
   ```
   Дальше Claude сам обновляет базу, если ей больше суток.

## Как пользоваться

1. Откройте папку `syteca-impact` в VS Code: **File → Open Folder**.
2. Откройте панель Claude Code (иконка Claude справа вверху или Ctrl+Esc).
3. Напишите:
   ```
   /impact https://jira.dev.local/jira/browse/AC-12345
   ```
   Можно несколько тикетов сразу и своё название рана: `/impact AC-1 AC-2 — один ран, назови его "ETR-1 - regression"`.
4. Claude покажет кейсы по тирам, дубли, устаревшие кейсы и черновики новых кейсов для непокрытых сценариев.
   Поправьте, что нужно, обычными словами («убери избыточные», «объедини в один end-to-end кейс»).
5. Напишите **«ок»** — только после этого Claude создаёт ран / новые кейсы в TestRail и даёт ссылку.

## Правила, которым следует Claude

Записаны в `CLAUDE.md` (общие для всей команды — если меняете, делайте это через pull request):
- ран строится по полю **Impact_Ekran**, а не по описанию бага;
- в ране нет избыточных кейсов: один кейс на одну проверку;
- новые кейсы — только в существующие папки по смыслу, на английском, в стиле соседних кейсов,
  тайтл `<Area> - <precondition> - <steps> - Check that ...` (до 250 символов), end-to-end, варианты — в ER;
- существующие кейсы никогда не редактируются и не удаляются;
- ничего не создаётся в TestRail без вашего явного «ок».

## Что не попадает в репозиторий

- `data/` — локальная копия кейсов (создаётся `sync.py`, ~60 MB);
- `runs/` — ваши личные списки ранов и черновики кейсов;
- `.claude/settings.local.json` — ваши личные настройки Claude Code;
- логины и пароли — только в Диспетчере учётных данных Windows.

## Если что-то не работает

| Ошибка | Что делать |
|---|---|
| `'py' is not recognized` | Переустановите Python с галочкой "Add python.exe to PATH" |
| `No module named 'keyring'` / `'requests'` | `py -m pip install -r requirements.txt` |
| `No credentials ... syteca-testrail` | `py -X utf8 scripts/set_credentials.py testrail` |
| `HTTP 401` | Неверный логин/пароль — повторите `set_credentials.py` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Убедитесь, что установлен `truststore` (входит в requirements.txt) и вы в корпоративной сети/VPN |
| TestRail отвечает таймаутом / HTTP 500 при создании кейсов | Повторите ту же команду — скрипт сам найдёт уже созданные кейсы и не сделает дублей |
