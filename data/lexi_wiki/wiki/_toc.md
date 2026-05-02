# Содержание Wiki

## 0. Входная точка

1. `wiki/index.md` — обзор, правила чтения, карта документации.

## 1. System Overview

1. `wiki/system-overview.md`
   - 1.1 Контекст продукта и runtime-контур
   - 1.2 Фактическая архитектура (as-is)
   - 1.3 Планируемая архитектура (to-be)
   - 1.4 Главные потоки данных
   - 1.5 Внешние интеграции
   - 1.6 Что считается source of truth
   - 1.7 Где уже есть расхождения
   - 1.8 Ограничения текущей модели

## 2. Components

1. `wiki/components.md`
   - 2.1 Точки входа и раннеры
   - 2.2 Telegram handlers и middleware
   - 2.3 Сервисный слой
   - 2.4 Репозитории и персистентность
   - 2.5 Конфигурация и assets
   - 2.6 Related Components (cross-links)
   - 2.7 Ограничения по каждому блоку

## 3. Data Models

1. `wiki/data-models.md`
   - 3.1 ORM-модели
   - 3.2 DTO-модели
   - 3.3 Redis-структуры и ключи
   - 3.4 Трансформации и сериализация
   - 3.5 Неявные контракты
   - 3.6 Частично устаревшие схемы из PRD

## 4. Pipelines / Workflows

1. `wiki/workflows.md`
   - 4.1 /start и инициализация пользователя
   - 4.2 Story creation FSM
   - 4.3 Генерация следующего story bit
   - 4.4 Vocabulary lookup и cache
   - 4.5 Story completion
   - 4.6 Health/readiness
   - 4.7 Failure points по цепочке

## 5-6-8-9. Decisions, R&D, Discussions, History

1. `wiki/strategy-and-rnd.md`
   - 5.1 Design decisions (почему выбрали именно так)
   - 5.2 Компромиссы и отвергнутые альтернативы
   - 6.1 Эксперименты (успешные/неуспешные)
   - 8.1 Internal discussions (сырые заметки команды)
   - 9.1 Историческая эволюция и рефакторинги
2. `wiki/internal-discussions.md`
   - отдельный неформальный журнал решений/опасений
3. `wiki/historical-evolution.md`
   - отдельная хронология изменений и дрейфа

## 7. Known Issues

1. `wiki/known-issues.md`
   - 7.1 Баги и потенциальные баги
   - 7.2 Ограничения runtime
   - 7.3 Нестабильные зоны
   - 7.4 Техдолг и наблюдения по тестам

## Bonus. RAG Evaluation

1. `wiki/questions.md`
   - простые вопросы
   - multi-hop вопросы
   - неоднозначные вопросы
   - вопросы с “устаревшими” предпосылками

## Теги для внутреннего поиска

- `#runtime`
- `#telegram`
- `#aiogram`
- `#fastapi`
- `#postgres`
- `#redis`
- `#openai`
- `#story-session`
- `#fsm`
- `#localization`
- `#moderation`
- `#techdebt`
- `#adr`
- `#experiments`
- `#rag-eval`

## Примечания по качеству

- Некоторые разделы умышленно частично пересекаются.
- Встречаются умеренные несовпадения между “как есть” и “как задумывалось”.
- Исторические notes не всегда синхронизированы с текущими путями модулей.

## Расширенная предметная карта

### Runtime/Platform

1. Запуск и bootstrap:
   - `lexi/main.py`
   - `lexi/runners/app.py`
2. Жизненный цикл:
   - `lexi/runners/polling.py`
   - `lexi/runners/webhook.py`
   - `lexi/runners/lifespan.py`
3. HTTP уровень:
   - `lexi/endpoints/telegram.py`
   - `lexi/endpoints/healthcheck.py`

### Telegram слой

1. Главные хендлеры:
   - `lexi/telegram/handlers/main/menu.py`
   - `lexi/telegram/handlers/story_creation.py`
   - `lexi/telegram/handlers/story_dialog.py`
2. Middleware:
   - `lexi/telegram/middlewares/user.py`
   - `lexi/telegram/middlewares/error_logger.py`
   - `lexi/telegram/middlewares/message_helper.py`
3. Filters / callback contracts:
   - `lexi/telegram/filters/*`
   - `lexi/telegram/keyboards/callback_data/*`

### Сервисный слой

1. Story creator:
   - модерация;
   - параметры истории;
   - language preference.
2. Story teller:
   - создание/продолжение истории;
   - vocabulary helper;
   - session lifecycle.
3. User service:
   - CRUD;
   - кэширование get;
   - валидация языков.

### Данные

1. SQL:
   - ORM `User`;
   - миграции Alembic.
2. Redis:
   - story session;
   - vocabulary cache;
   - FSM storage.
3. DTO:
   - user;
   - story;
   - healthcheck.

### Документы и артефакты

1. Product narrative:
   - `PRD.md`
2. Диаграммы:
   - `diagrams/as_is/*`
   - `diagrams/to_be/*`
3. Исторические notes:
   - `story_teller/STORY_CREATION_IMPLEMENTATION.md`

## Указатель по критическим вопросам

1. Где искать источник правды по runtime?
   - `wiki/system-overview.md`
2. Где искать зависимости между модулями?
   - `wiki/components.md`
3. Где искать описание сессий/схем/DTO?
   - `wiki/data-models.md`
4. Где искать шаги flow и точки отказа?
   - `wiki/workflows.md`
5. Где искать почему так сделали?
   - `wiki/strategy-and-rnd.md`
6. Где искать риски и техдолг?
   - `wiki/known-issues.md`
7. Где искать “сырые” командные оговорки?
   - `wiki/internal-discussions.md`
8. Где искать timeline изменений?
   - `wiki/historical-evolution.md`
9. Где искать набор RAG-вопросов?
   - `wiki/questions.md`

## Навигация по типу запроса

### Если вопрос продуктовый

- начать с `index`;
- проверить `strategy-and-rnd`;
- сопоставить с `workflows`.

### Если вопрос инженерный

- начать с `components`;
- затем `data-models`;
- затем `known-issues`.

### Если вопрос “почему расходится”

- сначала `system-overview`;
- потом `historical-evolution`;
- затем `internal-discussions`.

### Если вопрос для RAG-тестов

- сразу `questions`;
- потом выборочные страницы для проверки multi-hop.
