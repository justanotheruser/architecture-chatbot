# Data Models

## Общее

В проекте одновременно используются:

- SQLAlchemy-модель для персистентного профиля пользователя;
- Pydantic DTO для обмена внутри runtime;
- Redis-сериализация DTO через msgspec/pydantic адаптеры;
- контракты “по соглашению” в callback payload и в формате ответов LLM.

Это сочетание ускоряет MVP-итерации, но создает зону, где schema drift может появляться незаметно.

## 1) SQL schema (фактическая)

### Таблица `users`

Поля в runtime/миграциях:

- `id` (bigint, PK)
- `name`
- `language` (2-char код UI языка)
- `language_code` (оригинальный Telegram language code)
- `blocked_at`
- `created_at`
- `updated_at`
- `story_language_code` (появилось после rename миграции)
- `use_last_story_language` (bool)

### Миграционная эволюция

- init: создание `users`.
- add: `last_story_language_code`, `use_last_story_language`.
- rename: `last_story_language_code -> story_language_code`.

> В части тестов всё еще встречается старое имя поля.

## 2) ORM layer

### `User` (`models/sql/user.py`)

- наследует `Base` + `TimestampMixin`.
- имеет `dto()` для преобразования в `UserDto`.
- хранит только user-centric поля; story artifacts не сохраняет.

### Ограничения ORM слоя

- Нет моделей `stories`, `vocabulary_progress` в фактической БД.
- Нет явного soft-delete статуса кроме `blocked_at`.
- Нет нормализованной таблицы пользовательских экспериментов.

## 3) DTO: Пользователь

### `UserDto`

- поля совпадают с user-профилем;
- `url` и `mention` вычисляются on-demand;
- наследование от `ActiveRecordModel` используется для `model_state` при update.

### Трансформация

- ORM -> DTO через `User.dto()`.
- DTO -> update payload через `user.model_state` в `UserService.update`.

## 4) DTO: Story домен

### `StoryCreationParams`

- target language;
- protagonist;
- setting;
- native language.

### `StoryParams`

- языковые поля;
- prompt/runtime параметры (`openai_model`, `max_tokens`, `temperature`).

### `StoryLogic`

- `character_growths_moments_left` (счетчик вставок growth moments).

### `StorySession`

- `user_id`
- `params: StoryParams`
- `logic: StoryLogic`
- `story_text` (агрегированная история)
- `choices` (последние варианты выбора)
- `key_words` (список словарных слов по ходу истории)
- `turn_count`
- `created_at`, `last_updated`

### `StoryBit`

- текущий текст фрагмента;
- choices как список `StoryChoice`;
- key_words для inline кнопок.

### `VocabularyWord`

- слово;
- определение;
- перевод;
- language code.

## 5) Redis модели и ключи

### Ключ `story_session:*`

- тип: сериализованный `StorySession`.
- источник: `StorySessionKey`.
- lifecycle:
  - создается на старте story flow;
  - обновляется на каждом ходе;
  - удаляется при завершении.

### Ключ `vocabulary:*`

- тип: `VocabularyWord`.
- источник: `VocabularyCacheKey`.
- TTL: примерно 3600 секунд (1 час).

### Ключи cache wrapper

- для CRUD-путей используются префиксы формата `cache:<prefix>:...`.
- пример: `get_user` кэшируется декоратором `@redis_cache`.

## 6) Serialization и валидация

- RedisRepository:
  - `set` сериализует BaseModel через `model_dump(exclude_defaults=True)`;
  - `get` десериализует через `mjson.decode` + `TypeAdapter`.
- FSM storage:
  - RedisStorage aiogram с `json_loads/json_dumps` из `mjson`.

### Ограничения сериализации

- backward compatibility схем Redis-объектов не versioned.
- при эволюции DTO есть риск поломок старых сессий.

## 7) Неявные модели (implicit contracts)

### Контракт format LLM ответа для story

- ожидается story text + numbered choices (`1.`, `2.`).
- parser воспринимает первую нумерацию как переключение в режим choices.
- всё после этого может попасть в choices блок.

### Контракт format LLM ответа для vocabulary

- ожидаются строки:
  - `Definition: ...`
  - `Translation: ...`
- отклонения модели от этого формата дадут пустые поля.

### Контракт callback payload

- callback parsing иногда через typed wrappers (`CDStoryChoice`), иногда строкой.
- микс подходов делает интерфейс гибким, но не полностью единообразным.

## 8) Data transformations (примерные цепочки)

### User onboarding

1. Telegram user event.
2. `UserMiddleware` вызывает `UserService.get`.
3. Если user отсутствует -> `UserService.create`.
4. ORM User коммитится.
5. `UserDto` кладется в middleware context.

### Story creation

1. FSM собирает поля.
2. `StoryCreatorService` формирует `StoryCreationParams`.
3. `StoryTellerService` строит `StoryParams` + `StoryLogic`.
4. Сессия сохраняется в Redis как `StorySession`.

### Story continuation

1. Из callback извлекается `choice_id`.
2. Из `StorySession.choices` берется `choice_text`.
3. LLM генерирует продолжение.
4. Парсер выделяет story/choices.
5. Session обновляется и сериализуется обратно.

## 9) Частичные расхождения с PRD-схемой

PRD ожидает еще:

- `stories`
- `user_vocabulary_progress`

В runtime это пока частично “замещено” Redis session + логикой на лету.

## 10) Легкая избыточность (специально)

- Описание `story_language_code` есть и в `components`, и здесь.
- В `workflows` повторяется часть шагов про session lifecycle.
- В `known-issues` отдельно перечислены риски по парсингу/схемам.

## 11) Наблюдения по качеству моделей

- Плюс: DTO достаточно компактные и читаемые.
- Плюс: минимум сущностей ускоряет итерации.
- Минус: нет persisted history модели.
- Минус: schema evolution Redis пока ad hoc.
- Минус: тесты не полностью отражают текущее состояние namespace/полей.

## 12) TODO (модельный слой)

- [ ] Добавить version tag в Redis payload для story session.
- [ ] Решить, где хранить финальные stories.
- [ ] Нормализовать vocabulary progress в SQL (или явно отказаться).
- [ ] Зафиксировать формат LLM output через schema-aware parser.
- [ ] Причесать расхождения между PRD и текущими ORM/DTO.
