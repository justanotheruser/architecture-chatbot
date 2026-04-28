# System Overview

## 1) Назначение системы

Lexi — это Telegram-бот для детей (и родителей/наставников), где изучение языка встроено в интерактивный сторителлинг.  
Текущее ядро продукта: выбор языка истории, настройка героя и сеттинга, генерация сюжетных шагов, показ словаря по кнопкам.

## 2) Что реально работает сейчас (as-is)

- Runtime внутри `bot_server/lexi`.
- Основной execution path:
  - запуск через `python -m lexi.main`;
  - сборка `Bot` и `Dispatcher`;
  - выбор режима `webhook` или `polling`;
  - обработка Telegram updates.
- База данных: PostgreSQL, фактически используется таблица `users`.
- Сессии истории и FSM storage: Redis.
- Генерация текста/модерация: OpenAI API.
- Локализация: aiogram-i18n + Fluent (`assets/messages/*/*.ftl`).

## 3) Что фигурирует как план (to-be), но не стало частью runtime

- Celery worker/queue для генерации и тяжелых задач.
- Разделение Story Teller в отдельный сервисный контур.
- Event stream processor для аналитики прогресса истории.
- Автоматическая генерация обложки (image API) в конце истории.
- Более богатая модель persisted story/vocabulary progress в SQL.

## 4) Высокоуровневая архитектура

### Контур A: Telegram + App

- Telegram отправляет update.
- FastAPI endpoint (`TelegramRequestHandler`) проверяет секрет.
- Update передается в aiogram dispatcher.
- Middleware и routers решают, какой handler исполняется.
- Handler вызывает доменные сервисы.
- Результат возвращается пользователю через message/callback flow.

### Контур B: State + Persistence

- User profile хранится в PostgreSQL.
- Story session хранится в Redis (`story_session:*`).
- Vocabulary карточки кэшируются в Redis (`vocabulary:*`), TTL около часа.
- FSM aiogram тоже использует Redis storage.

### Контур C: LLM

- Story opening/continuation/conclusion генерируются через OpenAI chat completions.
- User-provided текст проходит модерацию через OpenAI Moderations API (если enabled).
- Ответы LLM парсятся простыми эвристиками (номерованные choices и т.п.).

## 5) Главные компоненты (крупные блоки)

- `main` + `runners`: сборка и запуск.
- `factory`: composition root (bot, dispatcher, i18n, services, session pool, redis).
- `telegram/handlers`: UX-логика и FSM.
- `services`: story creator/teller + CRUD + infra adapters.
- `models`: ORM + DTO.
- `endpoints`: webhook/health.
- `assets/messages`: тексты и локализация.
- `alembic`: миграции PostgreSQL.

## 6) Data flow (упрощённо)

1. Пользователь жмет кнопку “создать историю”.
2. FSM собирает параметры (язык/герой/сеттинг).
3. Валидация контента (moderation API).
4. Создается story session в Redis.
5. LLM генерирует стартовый кусок истории + варианты выбора.
6. Пользователь выбирает ветку -> генерируется следующий кусок.
7. По кнопкам словаря можно получить definition/translation.
8. По окончании story session удаляется.

## 7) Источники архитектурной правды

- Фактическое поведение:
  - `lexi/main.py`
  - `lexi/runners/app.py`
  - `lexi/factory/telegram/dispatcher.py`
  - `lexi/services/story_teller.py`
  - `lexi/telegram/handlers/story_creation.py`
  - `lexi/telegram/handlers/story_dialog.py`
- Целевое намерение:
  - `PRD.md`
  - `diagrams/to_be/*.puml`
- Текущая документная фиксация:
  - `diagrams/as_is/*.puml`
  - `story_teller/STORY_CREATION_IMPLEMENTATION.md` (частично устаревший путь `app/...`).

## 8) Наблюдаемые расхождения (важно)

- PRD обещает Celery и async jobs, runtime пока синхронный по части генерации story bit.
- PRD описывает таблицы `stories` и `user_vocabulary_progress`, миграции содержат только `users`.
- В тестах остались импорты `app.*`, хотя пакет называется `lexi`.
- В to-be диаграммах есть queue/pubsub/stream processor, в коде эти части не подключены.
- В doc-заметках встречается fuzzy language matching, текущий основной flow использует callback-коды языков.

## 9) Ограничения текущей архитектуры

- Ошибки внешнего LLM API напрямую влияют на UX (нет отдельного worker-контурa с retry policy).
- Парсинг choices основан на формате ответа модели; если модель “шалит”, разбор ломается.
- Story session целиком держится в Redis и не сохраняется как “финальный артефакт” в SQL.
- Финал истории не запускает image generation (есть TODO в handler).
- Набор автоматических тестов покрывает не все текущие модули и местами устарел.

## 10) Зависимости и их роль

- `aiogram`: маршрутизация Telegram events, middleware, FSM.
- `fastapi`/`uvicorn`: HTTP runtime и webhook endpoint.
- `sqlalchemy` + `asyncpg`: user persistence.
- `redis`: FSM + кэш + story session.
- `openai`: moderation + text generation.
- `aiogram-i18n` + `fluent-runtime`: локализация.
- `msgspec`: сериализация для redis storage.

## 11) Нюансы execution режима

- `use_webhook = true`: запускается route с секретом; incoming updates идут через FastAPI.
- `use_webhook = false`: запускается polling lifecycle, но FastAPI runtime всё равно стартует.
- При SIGTERM polling режим останавливается отдельной сигнализацией диспетчеру.
- Readiness учитывает внутренний флаг shutdown и состояние Redis.

## 12) Почему это важно для команды

- Текущая архитектура быстра для MVP и дешево меняется.
- Но границы компонентов пока “мягкие”, поэтому регрессии могут каскадно проходить через handlers/services.
- Для следующего этапа масштабирования нужна более строгая событийная модель и фоновые воркеры.

## 13) Связанные страницы

- Детализация по модулям: `wiki/components.md`
- Сущности и схемы: `wiki/data-models.md`
- Пайплайны и точки отказа: `wiki/workflows.md`
- Причины решений и эволюция: `wiki/strategy-and-rnd.md`
- Риски и проблемы: `wiki/known-issues.md`

## 14) Short field notes (внутренний лог наблюдений)

- [N-01] Режим webhook реализован аккуратно: есть `verify_secret`.
- [N-02] Для update processing используется background task set.
- [N-03] Риски race-condition минимальны, но мониторинг task exceptions неочевиден.
- [N-04] `shutdown_completed` используется и в runtime, и в readiness.
- [N-05] Проверка Redis встроена только в health endpoint.
- [N-06] Сигнальная обработка отличается для polling vs webhook path.
- [N-07] Dispatcher наполняется сервисами через workflow_data.
- [N-08] Это упрощает DI, но усложняет явные контракты модулей.
- [N-09] Story generation и moderation используют разные API clients, оба через OpenAI SDK.
- [N-10] Для vocabulary используется отдельный prompt и отдельный кэш-ключ.
- [N-11] TTL словаря фиксированный и пока не configurable из docs.
- [N-12] Локализация fallback-логики частично завязана на user language из БД.
- [N-13] При первом контакте пользователь создается middleware-слоем.
- [N-14] Это снижает boilerplate в handlers, но скрывает side-effects.
- [N-15] Набор FTL-файлов достаточно широкий по языкам интерфейса.
- [N-16] Story language и UI language концептуально разделены.
- [N-17] Эволюция поля `last_story_language_code -> story_language_code` зафиксирована миграцией.
- [N-18] В тестах ещё встречается старое имя этого поля.
- [N-19] Поддержка quiz-логики пока на уровне prompt helper.
- [N-20] В пользовательском flow quiz не подключен.
- [N-21] История заканчивается при turn-count логике в service (эвристика).
- [N-22] PRD говорит о token threshold, в коде это пока не видно.
- [N-23] Ключевые слова выделяются подчёркиванием, не bold.
- [N-24] Это расходится с ранней формулировкой в PRD.
- [N-25] Для story end используется callback `"menu"` строкой.
- [N-26] В остальном коде callback обычно типизирован через dataclass-like wrapper.
- [N-27] `deployment/docker-compose.yaml` поднимает app/db/redis, без worker.
- [N-28] В `.devcontainer` текстом упоминается Celery broker.
- [N-29] Значит инфраструктурный narrative опережает runtime-код.
- [N-30] Папка `event_stream_processor` пока пустая (заглушка).

## 15) Open questions по архитектуре

- Нужен ли отдельный сервис для story generation или достаточно worker-пула в том же репозитории?
- Как будем persist-ить финальную историю и промежуточные шаги: SQL, object storage или гибрид?
- Где хранить telemetry для образовательной аналитики?
- Когда добавляем idempotency и retry policy для LLM-calls?
- Как синхронизируем PRD и runtime без ручного дрейфа?

## 16) Дополнительные системные наблюдения

- В runtime нет явного circuit-breaker для внешнего API.
- Конфигурация поддерживает быстрое добавление env-полей, но часть фич может оставаться “мертвой” до внедрения кода.
- В текущей модели удобнее отлаживать happy path, чем edge cases.
- Для новых инженеров главный барьер — разнородные источники истины.
- На уровне deployment фактически три контейнера: app, db, redis.
- Наличие `event_stream_processor` директории пока больше сигнал roadmap, чем работающий контур.
- Health endpoints полезны, но не дают полного health графа зависимостей.
- Story completion в текущем виде логически финализирует сессию, но не материализует продуктовый артефакт.
- Это системно важно: пользователь может завершить историю, но команда не получает structured persisted результат.

## 17) Appendix: что проверять перед архитектурными изменениями

- совместимость callback contracts;
- влияние на story session schema;
- обратная совместимость миграций;
- влияние на readiness/liveness;
- деградацию UX при отказе внешних API;
- актуальность to-be диаграмм относительно новых решений;
- необходимость обновить known issues и questions.

## 18) Closing note

- Текущая система жизнеспособна для MVP, но требует дисциплины в синхронизации кода, docs и решений.
