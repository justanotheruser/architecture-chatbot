# Known Issues

## Важно

Этот раздел намеренно включает:

- подтвержденные проблемы;
- вероятные проблемные зоны;
- устаревшие артефакты, которые могут вводить в заблуждение.

## 1) Bugs / потенциальные баги

### K-01: Legacy imports в тестах

**Симптом:**

- несколько тестов импортируют `app.*`, хотя runtime пакет — `lexi.*`.

**Риск:**

- тесты не запускаются в чистой среде без shim-слоя.

**Затронуто:**

- `tests/test_story_creator.py`
- `tests/test_i18n.py`
- `tests/test_i18n_middleware.py`
- `tests/test_db_loading.py`
- `tests/test_error_logger.py`
- `tests/test_language_selection.py`

---

### K-02: Coverage target в pytest может быть устаревшим

**Симптом:**

- в `pyproject.toml` указан `--cov=app`.

**Риск:**

- некорректные отчеты покрытия или пустые метрики.

---

### K-03: isort first-party настройка не совпадает с текущим пакетом

**Симптом:**

- `known_first_party = ["app"]`.

**Риск:**

- шум в форматировании и CI стиль-проверках.

---

### K-04: Parser story response хрупок к формату модели

**Симптом:**

- разбор choices ожидает numbered list.

**Риск:**

- choices могут быть потеряны/искажены;
- flow continuation ломается на валидном, но “иначе оформленном” ответе.

---

### K-05: Vocabulary parser зависит от строковых префиксов

**Симптом:**

- ищутся `Definition:` / `Translation:`.

**Риск:**

- пустые поля при малейшем отклонении формата.

---

### K-06: Story end callback не полностью типизирован

**Симптом:**

- кнопка меню в story completion использует строку `"menu"` напрямую.

**Риск:**

- потенциальный drift с typed callback data подходом.

---

### K-07: TODO на генерацию обложки

**Симптом:**

- явный TODO в story end handler.

**Риск:**

- незавершенный продуктовый цикл;
- несоответствие ожиданиям из PRD.

---

### K-08: Timezone inconsistency в story session timestamps

**Симптом:**

- в одном месте `datetime.now(UTC)`, в другом `datetime.utcnow()`.

**Риск:**

- неоднородность временных меток и потенциальные сложности в аналитике.

## 2) Architectural limitations

- Нет persistent модели “финальной истории”.
- Нет очередей/воркеров для тяжелых задач в фактическом runtime.
- Нет строгого контракта schema versioning для Redis-сессий.
- Ограниченная observability по LLM interaction.

## 3) Product-function gaps (vs PRD)

- Нет quiz workflow в пользовательском диалоге.
- Нет image generation pipeline.
- Нет SQL таблиц для stories/vocabulary progress.
- Нет явного token-threshold механизма завершения истории.

## 4) Документационные несовпадения

- `to_be` диаграммы богаче текущего runtime.
- Исторический док `STORY_CREATION_IMPLEMENTATION` ссылается на старые пути `app/...`.
- В нескольких местах формулировки про “fuzzy matching языков” устарели относительно callback-based flow.

## 5) Нестабильные места

- Broad exception обработка в диалоговых handlers.
- Низкая предсказуемость LLM output на длинном контексте.
- Избыточная связанность handler <-> service <-> UI format.
- Потенциальные race при message edit в callback-сценариях.

## 6) CI / DX issues

- Тесты выглядят как набор smoke/manual scripts + частично unit-подход.
- Не везде прослеживается единый стиль тестирования.
- Исторические артефакты могут ломать “первый запуск” новых участников.

## 7) Operational risks

- External API downtime напрямую влияет на ключевой пользовательский flow.
- Redis как единая точка state при story диалоге.
- Отсутствие явной retry strategy для generation.
- Readiness покрывает Redis, но не обязательно всю цепочку зависимостей.

## 8) Severity snapshot

- High:
  - parser-contract fragility;
  - outdated test imports.
- Medium:
  - missing image generation;
  - docs/runtime drift.
- Low/Medium:
  - callback typing inconsistency;
  - timezone consistency.

## 9) Предлагаемые remediation шаги

- [ ] Починить namespace в тестах.
- [ ] Перевести coverage target на `lexi`.
- [ ] Ввести structured parsing protocol для LLM responses.
- [ ] Добавить telemetry вокруг parser failures.
- [ ] Либо реализовать image generation, либо явно убрать из пользовательских ожиданий.
- [ ] Синхронизировать docs-метки “as-is/to-be”.

## 10) Notes from incidents / near-incidents

- “Некоторые ответы модели уходили в narrative без choices — пользователи застревали.”
- “Были случаи, когда vocabulary definition приходила пустой из-за формата ответа.”
- “После изменений в структуре пакета часть тестов осталась неперенесенной.”
- “Новая команда несколько раз пыталась искать `app/` директорию по старым докам.”

## 11) What we monitor unofficially (пока неформально)

- Частота `story_session_expired`.
- Частота `invalid_choice`.
- Доля пустых/неполных vocabulary alerts.
- Средняя latency на story generation.
- Ошибки moderation API.

## 12) Статус по known issues

- Open: K-01..K-08.
- In discussion: structured outputs, worker strategy.
- Deferred: расширение SQL схемы под аналитические сценарии.

## 13) Примечание

- Этот список не исчерпывающий и обновляется по мере ревью runtime и документов.
