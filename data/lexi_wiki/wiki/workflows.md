# Pipelines / Workflows

## Введение

Этот документ описывает фактические операционные цепочки в проекте Lexi:

- как данные приходят;
- где трансформируются;
- где хранятся;
- где чаще всего возникают сбои.

Для архитектурного контекста смотреть также `wiki/system-overview.md`.  
Для сущностей — `wiki/data-models.md`.

## 1) Запуск приложения

### Pipeline

1. `python -m lexi.main`
2. Инициализация логгера.
3. Загрузка nested config (`AppConfig`).
4. Создание bot и dispatcher.
5. Проверка `telegram.use_webhook`.
6. Старт `run_webhook` или `run_polling`.
7. Запуск uvicorn.

### Failure points

- Ошибка чтения env.
- Невалидный токен Telegram.
- Невозможность подключиться к Redis/Postgres позже в runtime.

## 2) Webhook update ingestion

### Pipeline

1. Telegram вызывает POST endpoint.
2. `TelegramRequestHandler.handle` проверяет secret token.
3. Update уходит в `_handle_request_background`.
4. В фоне вызывается `dispatcher.feed_update`.
5. Handler возвращает ответ пользователю через aiogram.

### Failure points

- Секрет не совпал -> HTTP 401.
- Исключение в `feed_update` task может быть неочевидно для API-клиента.
- Неконсистентный state при резком shutdown.

## 3) Polling ingestion

### Pipeline

1. App стартует с polling lifecycle.
2. Dispatcher начинает long polling.
3. Updates проходят тот же middleware/handler путь.
4. При SIGTERM вызывается `_signal_stop_polling`.

### Failure points

- Потеря connectivity к Telegram API.
- Неожиданные состояния при одновременных lifecycle-хуках.

## 4) User bootstrap workflow

### Pipeline

1. Любой update с `event_from_user`.
2. `UserMiddleware` ищет user через `UserService.get`.
3. Если user не найден:
   - создается `User` в БД;
   - выбирается язык UI (telegram code или default locale).
4. `user` кладется в data context.

### Failure points

- Ошибка БД при создании пользователя.
- Конфликт состояния кэша (`get_user`) после частичных апдейтов.

## 5) Story creation FSM

### Шаги

1. Пользователь нажимает callback “create story”.
2. Проверяется default language preference.
3. Если preference нет:
   - state -> `selecting_language`;
   - показывается клавиатура языков.
4. Пользователь выбирает язык.
5. state -> `defining_protagonist`.
6. Пользователь вводит protagonist.
7. Проводится content moderation.
8. state -> `defining_setting`.
9. Пользователь вводит setting.
10. Повторная moderation.
11. Формируется `StoryCreationParams`.
12. Создается `StorySession` в Redis.
13. Генерируется initial story bit.
14. Отправляется сообщение с choices + vocabulary buttons.
15. FSM очищается.

### Failure points

- moderation API недоступен -> flow отклоняется.
- пользовательские данные отсутствуют в state -> KeyError.
- OpenAI completion вернул неожиданный формат.
- Redis write/read сбой при создании session.

## 6) Story continuation workflow

### Шаги

1. Пользователь выбирает choice.
2. Из callback извлекается `choice_id`.
3. Из Redis загружается `StorySession`.
4. Проверяется валидность `choice_id`.
5. Вызывается `continue_story`.
6. Иногда добавляется character development fragment (вероятностно).
7. На основе turn count выбирается continue/conclusion prompt.
8. Ответ LLM парсится на story text + choices.
9. Session обновляется (`story_text`, `choices`, `turn_count`, `key_words`).
10. Сообщение редактируется новым текстом и клавиатурой.

### Failure points

- session expired.
- invalid choice id.
- parser не выделил choices корректно.
- broad exception в handler скрывает точную природу сбоя.

## 7) Vocabulary lookup workflow

### Шаги

1. Пользователь нажимает кнопку `📖 word`.
2. Берется текущая story session для контекста.
3. Сначала проверяется Redis кэш (`vocabulary:*`).
4. Если miss:
   - вызывается LLM prompt для definition/translation;
   - парсится формат `Definition:` / `Translation:`;
   - результат кэшируется на 1 час.
5. Ответ показывается через `answer_callback_query(show_alert=True)`.

### Failure points

- miss + OpenAI ошибка.
- LLM отдал ответ в произвольном формате.
- кэш-промахи при неунифицированном ключе (разные регистры/формы слова).

## 8) Story end workflow

### Шаги

1. Пользователь триггерит `CDStoryEnd` (или choices заканчиваются).
2. Берется session.
3. Формируется completion message.
4. Показывается кнопка возврата в меню.
5. Session удаляется из Redis.

### Текущий gap

- Image generation не подключен (TODO в коде).
- Нету persisted артефакта “финальная история”.

## 9) UI language change workflow

### Шаги

1. Пользователь открывает language menu.
2. Выбирает locale callback или отправляет 2-символьный код.
3. `UserService.update` валидирует язык по `config.telegram.locales`.
4. Обновленный язык сохраняется в БД.

### Failure points

- Неподдерживаемый код.
- Неполный callback payload.
- stale data в кэше до очистки.

## 10) Story language preference workflow

### Шаги

1. Пользователь задает язык истории в меню.
2. Валидируется принадлежность к `available_languages`.
3. Обновляется `story_language_code`.
4. Следующий story creation может использовать это как default.

### Failure points

- Ошибка синхронизации между DTO/ORM и legacy тестами.
- Расхождение названий полей в исторических артефактах.

## 11) Health/readiness workflow

### Шаги

1. `/health/liveness` -> always alive payload.
2. `/health/readiness`:
   - проверяет `shutdown_completed`;
   - проверяет Redis доступность.
3. HTTP status зависит от состояния.

### Failure points

- Redis недоступен.
- readiness false во время shutdown window.

## 12) Internal operational notes

- В проде лучше трекать длительность LLM-calls отдельно по типу prompt.
- Нужен метрик-алерт на рост session expiry/invalid choice ошибок.
- Желателен sampling raw LLM outputs для диагностики parser drift.
- Для vocab flow полезно нормализовать слова (лемматизация/приведение регистра).

## 13) Сводка уязвимых точек по потоку

- Input:
  - пользовательский текст может быть неподходящим;
  - callback payload может быть malformed.
- Processing:
  - external API latency/failures;
  - parser assumptions о формате ответа.
- Storage:
  - Redis transient issues;
  - SQL latency/commit failures.
- Output:
  - редактирование message может падать при race (message deleted/changed).

## 14) Мини-чеклист для дебага

- Проверить текущий режим запуска (webhook/polling).
- Подтвердить, что `story_session` существует в Redis.
- Проверить корректность callback data.
- Снять raw response от LLM и сравнить с parser expectations.
- Убедиться, что locale и story_language валидны.
- Проверить логи error middleware и readiness endpoint.

## 15) Cross-page ссылки

- Компоненты, участвующие в каждом pipeline: `wiki/components.md`
- Модели данных в потоке: `wiki/data-models.md`
- Причины текущих компромиссов: `wiki/strategy-and-rnd.md`
- Список багов и нестабильностей: `wiki/known-issues.md`
