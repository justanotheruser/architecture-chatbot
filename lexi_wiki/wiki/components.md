# Components

## Карта модулей

- `lexi/main.py` — bootstrap.
- `lexi/runners/*` — запуск и lifecycle.
- `lexi/factory/*` — сборка runtime-зависимостей.
- `lexi/telegram/*` — handlers, keyboards, middlewares, filters.
- `lexi/services/*` — бизнес-логика и infra-доступ.
- `lexi/models/*` — ORM + DTO.
- `lexi/endpoints/*` — HTTP endpoints.
- `lexi/config/*` — env-конфиги.

## 1. Модуль: Main + Runners

### Purpose

- Централизованный запуск приложения.
- Переключение webhook/polling по конфигу.
- Настройка graceful shutdown.

### Internal structure

- `main.main()`:
  - инициализирует логгер;
  - читает `AppConfig`;
  - создает bot/dispatcher;
  - выбирает `run_webhook` или `run_polling`.
- `runners/app.py`:
  - содержит `run_app`;
  - регистрирует SIGTERM handler;
  - строит FastAPI app и wire-up состояния.

### Dependencies

- `AppConfig`
- `create_bot`, `create_dispatcher`
- `uvicorn`, `fastapi`, `aiogram`
- `TelegramRequestHandler` для webhook

### Limitations

- Логика запуска и runtime wiring смешаны в одном уровне.
- Нет явного разделения “control plane” и “request plane”.
- Поведение сигналов различается по режимам и требует ручного понимания.

### Related Components

- `factory/telegram/dispatcher.py`
- `endpoints/telegram.py`
- `runners/polling.py`, `runners/webhook.py`, `runners/lifespan.py`

---

## 2. Модуль: Factory Layer

### Purpose

- Собрать все runtime-зависимости в одном месте.
- Дать dispatcher готовые сервисы, storage и middleware.

### Internal structure

- `factory/services.py`:
  - создает `RedisRepository`;
  - создает `UserService`, `StoryCreatorService`, `StoryTellerService`.
- `factory/telegram/dispatcher.py`:
  - инициализирует RedisStorage для FSM;
  - инжектит `config`, `assets`, `session_pool`, `redis`;
  - подключает routers и middlewares.
- `factory/telegram/i18n.py`:
  - строит FluentRuntimeCore;
  - создает i18n middleware + user manager.

### Dependencies

- `redis.asyncio.Redis`
- `sqlalchemy async_sessionmaker`
- `aiogram_i18n`
- `assets/messages` и `assets/commands.yml`

### Limitations

- Слабая типизация workflow_data на уровне “все в один объект”.
- Часть зависимостей неявно ожидается в handler-подписях.
- При расширении набора сервисов появляется риск namespace collisions в data.

### Related Components

- `services/*`
- `telegram/handlers/*`
- `config/env/*`

---

## 3. Модуль: Telegram Handlers

### Purpose

- Реализовать пользовательские сценарии в Telegram UI.
- Управлять FSM story creation и story dialog.

### Internal structure

- `handlers/main/menu.py`:
  - `/start`, `/language`, `/story_language`;
  - callback-обработка смены языков.
- `handlers/story_creation.py`:
  - FSM состояния: language -> protagonist -> setting;
  - валидация контента через `StoryCreatorService`;
  - запуск initial story generation.
- `handlers/story_dialog.py`:
  - выбор веток сюжета;
  - словарь по callback;
  - завершение истории + очистка сессии.
- `handlers/admin/*`:
  - каркас для админ-функций (минимально заполнен).

### Dependencies

- aiogram routers/filters/FSM
- `StoryCreatorService`, `StoryTellerService`, `UserService`
- i18n контекст
- callback data классы из `telegram/keyboards/callback_data/*`

### Limitations

- Есть broad exception handlers (общий catch).
- Финал истории имеет TODO вместо завершенной async-цепочки.
- Часть UX-линий зависит от строгого формата ответа LLM.

### Related Components

- `services/story_creator.py`
- `services/story_teller.py`
- `telegram/middlewares/*`
- `assets/messages/*`

---

## 4. Модуль: Telegram Middlewares

### Purpose

- Вынести cross-cutting concerns из handlers.
- Унифицировать context data (user, i18n, helper, error logging).

### Internal structure

- `UserMiddleware`:
  - загружает/создает пользователя;
  - кладет `user` в data.
- `ErrorLoggerMiddleware`:
  - журналирует исключения.
- `MessageHelperMiddleware`:
  - дает helper для унифицированных ответов.
- `event_typed.py`:
  - базовый типизированный слой для middleware стека.

### Dependencies

- `UserService`
- aiogram middleware API
- i18n middleware

### Limitations

- Скрытые side-effects (создание user на любом событии с `from_user`).
- Потенциальная сложность дебага из-за глубокого middleware chain.

### Related Components

- `services/crud/user.py`
- `utils/localization/manager.py`
- `telegram/handlers/*`

---

## 5. Модуль: StoryCreatorService

### Purpose

- Проверка пользовательских вводов.
- Управление language preference пользователя.
- Сбор `StoryCreationParams`.

### Internal structure

- `validate_content_moderation`:
  - использует OpenAI Moderation API;
  - при ошибке API возвращает `False` (консервативный путь).
- `update_user_language_preference`:
  - обновляет `story_language_code`.
- `create_story_params`:
  - собирает DTO с validated полями.

### Dependencies

- `UserService`
- `content_moderation` конфиг
- OpenAI client

### Limitations

- Отказ moderation API = отказ flow (строгий подход).
- Нет fallback-провайдера или ретраев.

### Related Components

- `handlers/story_creation.py`
- `models/dto/story_creation_params.py`
- `models/dto/user.py`

---

## 6. Модуль: StoryTellerService

### Purpose

- Ведение story session.
- Генерация story chunks и vocabulary helper.

### Internal structure

- session operations:
  - `create_story_session`
  - `get_story_session`
  - `update_story_session`
  - `delete_story_session`
- generation operations:
  - `generate_initial_story`
  - `continue_story`
  - `get_vocabulary_definition`
- utility operations:
  - `_parse_story_response`
  - `_extract_key_words`
  - `format_story_text_with_key_words`

### Dependencies

- `RedisRepository`
- OpenAI chat completions
- prompts из `lexi/prompts.py`

### Limitations

- Parsing choices зависит от regex `^\d+\.` и может быть хрупким.
- Выделение ключевых слов примитивное (длина слова > 5, фактически первые 1-2).
- Есть смешение timezone подходов (`now(UTC)` и `utcnow()` в разных местах).
- Нет отдельного шага валидации корректности structure ответа LLM.

### Related Components

- `handlers/story_dialog.py`
- `models/dto/story.py`
- `services/redis/repository.py`

---

## 7. Модуль: UserService + Postgres Layer

### Purpose

- CRUD пользователя.
- Кэширование user retrieval.

### Internal structure

- `UserService.create/get/update/count`
- `SQLSessionContext` (repository + uow)
- `UsersRepository`
- `UoW`

### Dependencies

- SQLAlchemy async engine/session pool
- Redis (для `@redis_cache`)
- `models/sql/user.py`, `models/dto/user.py`

### Limitations

- Кэш-ключ формируется из позиционных/именованных аргументов без versioning.
- Данные user-модели пока ограничены и не покрывают story progress.

### Related Components

- `telegram/middlewares/user.py`
- `telegram/handlers/main/menu.py`
- `factory/services.py`

---

## 8. Модуль: Endpoints

### Purpose

- HTTP граница для webhook и health.

### Internal structure

- `endpoints/telegram.py`:
  - проверка секрета;
  - асинхронная отправка update в dispatcher.
- `endpoints/healthcheck.py`:
  - liveness/readiness;
  - проверка Redis и lifecycle-флагов.

### Dependencies

- FastAPI
- aiogram dispatcher/bot
- RedisRepository

### Limitations

- Нет расширенной диагностики (например, SQL readiness).
- Ошибки feed_update задач не всегда видны в API-ответах.

### Related Components

- `runners/app.py`
- `factory/telegram/fastapi.py`

---

## 9. Модуль: Config + Assets

### Purpose

- Централизованный env-driven runtime config.
- Сбор команд и локализации.

### Internal structure

- `config/env/app.py` агрегирует nested settings.
- `config/assets.py` загружает YAML assets.
- `const.py` содержит пути и time constants.
- FTL локали расположены в `assets/messages`.

### Dependencies

- Pydantic settings
- yaml loader
- Fluent runtime

### Limitations

- Легко получить “конфиг есть, кода нет” (например, для planned features).
- Список supported locales/languages критичен для стабильности UX.

### Related Components

- `factory/telegram/i18n.py`
- `handlers/main/menu.py`
- `services/story_creator.py`

---

## 10. Краткая матрица связей (for orientation)

- `handlers/story_creation` -> `StoryCreatorService` + `StoryTellerService`
- `StoryCreatorService` -> `UserService` + Moderation API
- `StoryTellerService` -> Redis + OpenAI + prompts
- `UserService` -> SQL repositories + Redis cache
- `UserMiddleware` -> `UserService.create/get`
- `run_webhook` -> `TelegramRequestHandler`
- `setup_fastapi` -> health routes + app.state wiring

## 11. Наблюдения по зрелости компонентов

- Раннеры: стабильные.
- Handlers: функциональные, но быстро менялись, есть долг по унификации.
- Story services: работают, но чувствительны к формату LLM output.
- Persistence: минималистичная модель, норм для MVP.
- Тесты: частично legacy, не всегда бьются с текущей структурой пакетов.

## 12. Что пересмотреть в следующем цикле

- Явные интерфейсы сервисов в dispatcher workflow_data.
- Слой нормализации/валидации LLM output.
- Вынесение image generation и quiz logic в фоновые задачи.
- Приведение тестов и docs к актуальному namespace `lexi`.
