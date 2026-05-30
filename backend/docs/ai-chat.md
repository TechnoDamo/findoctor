# AI-чат: архитектура и поток запросов

AI-чат ФинДоктора — ассистент с поддержкой текста и голоса. Пользователь отправляет текстовое или аудио-сообщение, backend вызывает STT/LLM/TTS-провайдеров и возвращает ответ. Дополнительно может включаться поток рекомендаций с RAG и поиском.

## Обзор

```text
POST /api/v1/ai/chat/messages  (JSON: текст или base64-аудио)
POST /api/v1/ai/chat/audio      (multipart/form-data: голос)
  │
  ├── STT         — аудио → текст (gpt-4o-audio-preview или свой провайдер)
  ├── LLM         — текст → ответ (gpt-4o или свой провайдер)
  ├── TTS         — ответ → аудио (gpt-4o-audio-preview, SSE-стриминг, PCM16→WAV)
  │
  └── (опционально) Рекомендательный оркестратор
       ├── Planner LLM   — решает, нужны ли RAG/Search
       ├── RAGFlow       — retrieval из проиндексированной базы знаний
       ├── SearXNG        — поиск в разрешённых источниках
       └── Finalizer LLM — формирует ответ на основе evidence
```

По умолчанию рекомендации выключены: `RECOMMENDATIONS_ENABLED=false`. Без них работает простой путь — один LLM-вызов.

---

## Точки входа

Файл: `backend/app/api/routes/ai_chat.py`

| Метод  | Путь                                    | Аутентификация | Описание                                |
|--------|-----------------------------------------|----------------|-----------------------------------------|
| `POST` | `/api/v1/ai/chat/messages`             | Bearer JWT     | Текст или base64-аудио                  |
| `POST` | `/api/v1/ai/chat/audio`                | Bearer JWT     | Голос через multipart/form-data         |
| `GET`  | `/api/v1/ai/chat/conversations`        | Bearer JWT     | Список диалогов с пагинацией            |
| `POST` | `/api/v1/ai/chat/conversations`        | Bearer JWT     | Создать пустой диалог                   |
| `GET`  | `/api/v1/ai/chat/conversations/{id}`   | Bearer JWT     | Диалог с сообщениями                    |
| `DELETE` | `/api/v1/ai/chat/conversations/{id}` | Bearer JWT     | Удалить диалог (каскадно)               |

Аутентификация — через `CurrentUser` зависимость (`app/api/dependencies.py`):
- JWT Bearer: декодирование токена, проверка сессии в `auth_sessions`, проверка пользователя в `users`.
- Альтернативно: заголовки `X-FinDoctor-Email` + `X-FinDoctor-Password` (simple auth, для разработки).

Каждый запрос получает `DbConnection` — соединение с БД из пула, обёрнутое в транзакцию.

---

## Текстовый запрос: полный поток

### Схема запроса

Файл: `backend/app/schemas/ai_chat.py` — `AiChatRequest` (camelCase через alias-генератор):

```json
{
  "conversationId": "uuid или null (создать новый)",
  "title": "заголовок нового диалога",
  "input": [
    {"type": "text", "text": "Привет, проанализируй мои расходы"},
    {"type": "audio", "text": "подсказка для STT", "audio": {"base64": "...", "format": "wav"}}
  ],
  "responseModalities": ["text", "audio"],
  "audioResponse": {"voice": "echo", "format": "pcm16", "delivery": "temporary_url"},
  "context": {
    "includeAccounts": true,
    "includeTransactions": true,
    "dateFrom": "2025-01-01",
    "dateTo": "2025-12-31"
  }
}
```

### Пошаговый проход

Файл: `backend/app/services/ai_chat.py` — функция `send_message()`.

**1. Разрешение диалога**

```python
if conversation_id is None:
    conversation = await chat_repo.insert_conversation(conn, user_id, title)
else:
    conversation = await chat_repo.find_conversation(conn, conversation_id)
    if conversation is None or conversation["user_id"] != user_id:
        raise NotFoundError("Диалог не найден")
```

Без `conversation_id` создаётся новая запись в `ai_chat_conversations`.

**2. Сохранение сообщения пользователя**

```python
chat_repo.insert_message(conn, conversation_id, "user", input_parts)
```

Сохраняет `input_parts` как JSONB в `ai_chat_messages.content`.

**3. Извлечение текста**

```python
user_text = _text_from_input_parts(input_parts)
```

Конкатенирует все части с `type == "text"`.

**4. STT (если есть аудио-часть)**

Если среди `input_parts` есть `{"type": "audio", "audio": {...}}`:

```python
transcript, stt_usage = await _run_stt(audio_data, audio_format, prompt)
user_text = "\n".join([user_text, transcript]).strip()
```

STT отправляет запрос к OpenAI-совместимому API (`chat/completions`) с `input_audio`:
- Модель: `stt_model` или fallback на `gpt-4o-audio-preview`
- Промпт: `prompts/stt_system.txt` — «Транскрибируй аудио пользователя точно. Сохраняй исходный язык. Не переводи.»

**5. LLM (или Рекомендации)**

```python
assistant_text, llm_usage, tool_results = await _run_text_or_recommendation(
    user_text=user_text,
    financial_context=financial_context,
    prompt_name="llm_text",
)
```

Функция `_run_text_or_recommendation` (строка 388) — **точка ветвления**:

```python
if not settings.recommendations_enabled:
    assistant_text, usage = await _run_llm(user_text, financial_context, prompt_name)
    return assistant_text, usage, []

# Рекомендации включены
from app.services.recommendations.orchestrator import run_recommendation_flow
return await run_recommendation_flow(user_text, financial_context, prompt_name)
```

Подробнее о ветке рекомендаций — далее.

**6. TTS (если запрошено аудио)**

Если `"audio" in response_modalities`:

```python
audio_payload = await _run_tts(
    _truncate_for_tts(assistant_text),
    voice=audio_response.get("voice"),
    response_format=audio_response.get("format"),
)
```

TTS вызывает `chat/completions` с `stream: true` и `modalities: ["text", "audio"]`:
- Модель: `tts_model` или fallback на `gpt-4o-audio-preview`
- Промпт: `prompts/tts_system.txt` — «озвучь точный текст ассистента, тёплый спокойный тон, русский акцент»
- Формат: PCM16-стриминг через SSE → сборка чанков → обёртка в WAV (функция `_wav_from_pcm16`, 44-байтный RIFF-заголовок + PCM-сэмплы)
- Ответ кодируется обратно в base64

Обрезка текста (`_truncate_for_tts`, строка 370): текст длиннее `TTS_MAX_CHARS` (300 по умолчанию) обрезается до последнего целого предложения.

**7. Сохранение ответа ассистента**

```python
assistant_parts = [{"type": "text", "text": assistant_text, "audio": audio_payload}]
chat_repo.insert_message(conn, conversation_id, "assistant", assistant_parts)
chat_repo.touch_conversation(conversation_id)  # обновляет updated_at
```

**8. Ответ**

```json
{
  "conversationId": "uuid",
  "userMessageId": "uuid",
  "assistantMessageId": "uuid",
  "requestText": "транскрипт или исходный текст",
  "output": {
    "text": "ответ ассистента",
    "audio": {"contentType": "audio/wav", "format": "wav", "base64": "...", "url": null},
    "transcript": "транскрипт (если был STT)",
    "requestText": "транскрипт или исходный текст"
  },
  "toolResults": [],
  "usage": {"inputTokens": 150, "outputTokens": 80}
}
```

---

## Голосовой запрос: отличия

Файл: `backend/app/services/ai_chat.py` — функция `send_voice_message()`.

Отличия от текстового:
- Принимает `UploadFile` через `POST /api/v1/ai/chat/audio` (multipart/form-data)
- Backend читает байты и кодирует в base64
- `input_parts` всегда: `[{"type": "audio", "text": prompt, "audio": {"contentType": "wav", "base64": "..."}}]`
- Использует `prompt_name="llm_voice"` — разговорный стиль, без маркдауна, короткие ответы
- `response_modalities` по умолчанию `["audio", "text"]` — аудио-ответ включён всегда
- `financial_context` не передаётся (всегда `None`)

---

## Промпты

Файлы: `backend/app/prompts/`

| Файл                     | Роль                                   |
|--------------------------|----------------------------------------|
| `llm_text.txt`           | LLM для текстового режима              |
| `llm_voice.txt`          | LLM для голосового режима              |
| `stt_system.txt`         | Инструкция для speech-to-text          |
| `tts_system.txt`         | Инструкция для text-to-speech          |
| `recommendation_planner.txt`     | Planner: решить, нужны ли инструменты  |
| `recommendation_finalizer.txt`   | Finalizer: синтез из evidence          |
| `recommendation_context_policy.txt` | Правила учёта фин. контекста      |
| `recommendation_safety_policy.txt` | Предостережения (не гарантировать, не выдавать за проф. совет) |

`llm_text.txt`:
```
Ты — финансовый ассистент ФинДоктора.
У тебя мужской пол.
Отвечай ясно и кратко.
Используй русский язык, когда пользователь пишет или говорит по-русски.
Если финансовых данных не хватает, скажи, какая информация нужна, и не выдумывай числа.
```

`llm_voice.txt`:
```
Ты — голосовой финансовый ассистент ФинДоктор. Твой пол — мужской.
Отвечай коротко. Без маркдауна. Разговорным языком.
Никогда не используй символы форматирования.
```

Функция `_build_system_prompt()` (строка 377) собирает системный промпт: базовый из файла + финансовый контекст, если передан клиентом.

---

## Конфигурация провайдеров

Файл: `backend/app/services/ai_chat.py` — `_provider_config(kind)` (строка 22)

Для каждого `kind` (`"llm"`, `"stt"`, `"tts"`) настройки собираются с fallback:

```python
base_url = settings.{kind}_base_url  or settings.openai_base_url
api_key  = settings.{kind}_api_key   or settings.openai_api_key
model    = settings.{kind}_model     or (
    settings.openai_audio_model if kind in {"stt", "tts"}
    else settings.openai_text_model
)
```

Это значит: можно указать отдельные URL/ключ/модель для LLM, STT и TTS, либо использовать общие OpenAI-настройки.

### Переменные окружения

Файл: `backend/app/settings.py`

```env
# Базовые OpenAI (общий fallback)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_TEXT_MODEL=gpt-4o
OPENAI_AUDIO_MODEL=gpt-4o-audio-preview

# Отдельные провайдеры (переопределяют базовые)
LLM_API_KEY=...
LLM_BASE_URL=...
LLM_MODEL=...

STT_API_KEY=...
STT_BASE_URL=...
STT_MODEL=...

TTS_API_KEY=...
TTS_BASE_URL=...
TTS_MODEL=...
TTS_VOICE=echo
TTS_MAX_CHARS=300

# Рекомендации
RECOMMENDATIONS_ENABLED=false
RECOMMENDATION_PLANNER_MODEL=...
RECOMMENDATION_FINALIZER_MODEL=...
```

### HTTP-клиент

Файл: `backend/app/clients/http.py`

Все вызовы к LLM/STT/TTS идут через глобальный `httpx.AsyncClient` (singleton):
- `timeout=120s`, `connect=10s`
- `max_keepalive_connections=10`, `max_connections=50`

Две обёртки в `services/ai_chat.py`:
- `_chat_completion(kind, payload)` — обычный POST, таймаут 120s
- `_chat_completion_sse(kind, payload)` — POST без таймаута, возвращает сырой текст SSE-потока (для TTS)

### Абстрактные клиенты (не используются в проде)

Файлы: `backend/app/clients/llm/base.py`, `backend/app/clients/llm/openai.py`

`BaseLlmClient` (абстрактный класс) и `OpenAiLlmClient` (реализация) **существуют в кодовой базе, но НЕ используются сервисным слоем**. Сервис `ai_chat.py` вызывает `_chat_completion()` напрямую, минуя этот слой. Клиенты оставлены для будущего рефакторинга, когда STT/LLM/TTS логика будет вынесена из сервиса в специализированные клиенты.

---

## Рекомендательный оркестратор

Файл: `backend/app/services/recommendations/orchestrator.py`

Включается флагом `RECOMMENDATIONS_ENABLED=true`. Заменяет одиночный LLM-вызов на трёхфазный поток.

### Фаза 1: Planner LLM (`_run_planner`, строка 80)

Первый LLM-вызов с `temperature=0` и `response_format={type: "json_schema", strict: true}`.

Системный промпт: `recommendation_planner.txt` + `recommendation_context_policy.txt` + `recommendation_safety_policy.txt`.

Модель обязана вернуть строгий JSON (схема в `schemas.py`):

```json
{
  "response_text": "ответ, если инструменты не нужны",
  "needed_tools": {
    "rag": {"rag_requests": ["query 1", "query 2"]},
    "search": {"search_queries": ["site:cbr.ru consumer debt"]}
  }
}
```

`needed_tools` может быть `null` — тогда ответ отдаётся сразу, без дальнейших фаз.

### Фаза 2: Выполнение инструментов (`_execute_tools`, строка 112)

Выполняется **только если** `plan.needed_tools is not None`.

Порядок:
1. **RAGFlow** (если запрошен): для каждого `rag_request` (до `RECOMMENDATION_MAX_RAG_REQUESTS=3`) — `POST <ragflow_base_url>/api/v1/retrieval` с параметрами `dataset_id`, `query`, `page_size`.
2. **SearXNG** (если запрошен): для каждого `search_query` (до `RECOMMENDATION_MAX_SEARCH_QUERIES=3`) — `GET <searxng_base_url>/search?q=...&format=json`, затем фильтрация результатов по `allowed_hosts` из `ragflow/allowed_resources.txt`.

Результаты обрезаются до `RECOMMENDATION_MAX_EVIDENCE_ITEMS=8`.

### Фаза 3: Finalizer LLM (`_run_finalizer`, строка 147)

Второй LLM-вызов — синтез ответа из evidence.

Системный промпт: `<prompt_name>.txt` + `recommendation_context_policy.txt` + `recommendation_safety_policy.txt` + `recommendation_finalizer.txt`.

На вход подаётся JSON:
```json
{
  "user_text": "оригинальный вопрос",
  "financial_context": {...},
  "planner_response": "предварительный ответ планера",
  "evidence": [{"source": "ragflow", "query": "...", "title": "...", "url": "...", "text": "...", "score": 0.82}]
}
```

Evidence обрезается до `RECOMMENDATION_MAX_EVIDENCE_CHARS=12000` посимвольно.

### Возврат

Оркестратор возвращает кортеж `(final_text, суммарный_usage, tool_results)`, где `tool_results` содержит и план, и список evidence:

```json
[
  {"type": "recommendation_plan", "plan": {...}},
  {"type": "recommendation_evidence", "items": [...]}
]
```

### Сценарии без Finalizer

Есть ровно один: когда planner вернул `needed_tools: null`. Тогда ответ планера (`plan.response_text`) возвращается как финальный, инструменты не вызываются, finalizer не запускается. Суммарно **1 LLM-вызов** вместо трёх.

Если `needed_tools` не null — инструменты вызываются всегда, и finalizer запускается всегда, **независимо от содержимого результатов** инструментов.

---

## База данных

### Таблицы

Миграция: `backend/migrations/versions/20260529_0003_auth_sessions_and_ai_chat.py`

```sql
CREATE TABLE ai_chat_conversations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ai_chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES ai_chat_conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,          -- 'user' или 'assistant'
    content         JSONB NOT NULL,         -- массив частей [{type, text, audio}]
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_chat_messages_conversation
    ON ai_chat_messages(conversation_id, created_at);
```

Удаление диалога каскадно удаляет все его сообщения.

### Запросы

Файл: `backend/app/db/queries/ai_chat.sql` — 9 именованных запросов

| Запрос                 | Описание                                         |
|------------------------|--------------------------------------------------|
| `list_conversations`   | Список диалогов с `last_message_preview` и пагинацией |
| `count_conversations`  | Количество диалогов для пагинации                |
| `find_conversation`    | Диалог по id                                     |
| `insert_conversation`  | Создать (`gen_random_uuid()`)                    |
| `update_conversation`  | Обновить заголовок                               |
| `delete_conversation`  | Удалить (каскадно)                               |
| `list_messages`        | Сообщения диалога (сортированы по `created_at`)  |
| `insert_message`       | Добавить сообщение (`gen_random_uuid()` + JSONB)   |
| `touch_conversation`   | Обновить `updated_at`                            |

Репозиторий: `backend/app/repositories/ai_chat.py` — простые обёртки над запросами, принимают `AsyncConnection` от вызывающего кода.

---

## Фронтенд

### Страница чата

Файл: `frontend/src/app/dashboard/chat/page.tsx`

Два режима:
- **Текстовый**: поле ввода + кнопка «Отправить». Вызывает `POST /ai/chat/messages`.
- **Голосовой**: полноэкранная кнопка записи (`VoiceButton`). Вызывает `POST /ai/chat/audio` через FormData.

Текстовый поток:
1. `sendText()` — отправляет `{input: [{type: "text", text}], responseModalities: ["text"]}`
2. При ответе: отображает текст, если есть `audio.base64` — воспроизводит через `<audio>` элемент

Голосовой поток:
1. `useAudioRecorder` (Web Audio API) записывает микрофон → WAV Blob
2. `handleVoiceAudio(blob)` — отправляет `FormData` с `audio`, `audioFormat: "wav"`, `responseModalities: "text,audio"`
3. При ответе: заменяет плейсхолдер «🎤 Распознавание...» на транскрипт, отображает текст, воспроизводит аудио

### Аудио-запись

Файл: `frontend/src/lib/hooks/use-audio-recorder.ts`

- `getUserMedia({audio: true})` → `AudioContext.createScriptProcessor(4096)`
- RMS-амплитуда для визуализации громкости
- Детекция тишины: `SILENCE_THRESHOLD=0.08`, `SILENCE_DURATION_MS=1500` (настраивается через `NEXT_PUBLIC_VOICE_*`)
- Кодирование: Float32Array → WAV через ручной DataView (44-байтный заголовок + int16 PCM)
- В seamless-режиме (`NEXT_PUBLIC_VOICE_AUTO_RESTART=true`) запись перезапускается автоматически после окончания воспроизведения ответа

### API-клиент

Файл: `frontend/src/lib/api/client.ts`

Axios с `baseURL=<NEXT_PUBLIC_API_URL>/api/v1`:
- **Request interceptor**: добавляет `Authorization: Bearer <access_token>` и/или `X-FinDoctor-Email` + `X-FinDoctor-Password`
- **Response interceptor**: при 401 (если не auth-эндпоинт) пытается обновить токен через `POST /auth/refresh`, затем повторяет исходный запрос. При неудаче — очищает auth и редиректит на `/auth/login`

---

## Middleware и логирование

### CORS

Файл: `backend/app/main.py` — `CORSMiddleware`:
- `allow_origins`: из `CORS_ORIGINS` (по умолчанию `http://localhost:3000`)
- `allow_credentials=true`, все методы, все заголовки

### Логирование HTTP

Файл: `backend/app/core/request_logging.py` — `HttpLoggingMiddleware`:

Каждый запрос:
1. Генерирует `X-Request-ID`
2. Логирует `REQUEST: <method> <path>` с заголовками и телом (если включено)
3. Логирует `RESPONSE: <status> <method> <path> <duration_ms>ms` с заголовками и телом

Тела в не-UTF8 кодируются в base64.

Настройки:
```env
LOG_HTTP_HEADERS=true
LOG_HTTP_BODIES=true
LOG_RESPONSE_HEADERS=true
LOG_RESPONSE_BODIES=true
```

### Обработка ошибок БД

Файл: `backend/app/main.py` — глобальные exception handlers:
- `AppError` → JSON `{error: {code, message, details}}` с соответствующим статусом
- `UniqueViolation` → 409 Conflict
- `ForeignKeyViolation` → 409 Conflict
- Остальные `PsycopgError` → 400 Bad Request

---

## Тесты

Файл: `backend/tests/test_ai_chat.py` — 2 интеграционных теста:

- `test_send_text_message_uses_contract_camel_case` — проверяет camelCase-контракт, сохранение в БД, роли сообщений
- `test_send_text_message_continues_existing_camel_case_conversation` — проверяет продолжение существующего диалога

Оба используют `monkeypatch` на `_run_llm` для мокирования LLM-ответа.

Запуск:
```bash
uv run python test_runner.py --ai_chat
# или
uv run pytest tests/test_ai_chat.py -q
```

---

## Нюансы и принятые решения

### Прямые вызовы вместо клиентов

`BaseLlmClient` / `OpenAiLlmClient` (`clients/llm/`) существуют, но сервис `ai_chat.py` их **не использует**. Вместо этого вызывает `_chat_completion()` напрямую. Причина: сервисный слой управляет оркестрацией STT→LLM→TTS, и каждый шаг идёт к потенциально разным провайдерам через `_provider_config(kind)`. Абстрактный клиент не покрывает этот сценарий без переделки.

### Транзакция охватывает LLM-вызовы

`DbConnection` оборачивает весь обработчик в транзакцию (`pool.py:89` — `async with conn.transaction()`). Это значит, что LLM/STT/TTS-вызовы происходят внутри открытой транзакции БД, что противоречит правилу из `STACK.md`: «Avoid external network calls inside open database transactions». Это компромисс: если LLM отвечает 30 секунд, транзакция висит всё это время. При росте нагрузки стоит вынести LLM-вызовы за транзакцию: сохранить user-сообщение и закоммитить до LLM, а assistant-сообщение — отдельной транзакцией после.

### TTS стриминг и формат

TTS получает PCM16 через SSE, собирает чанки и оборачивает в WAV на стороне backend. Это сделано для совместимости с фронтендом: браузерный `<audio>` не воспроизводит сырой PCM16. WAV-заголовок формируется вручную (`_wav_from_pcm16`, 44 байта).

### Ограничение длины TTS

`TTS_MAX_CHARS=300` — текст длиннее 300 символов обрезается до последнего целого предложения перед точкой. Это ограничение модели TTS: `gpt-4o-audio-preview` принимает ограниченный объём текста для озвучки.

### Рекомендации: отсутствие условного выполнения инструментов

Если planner запросил RAG и Search — выполняются **оба**, независимо от того, вернул ли RAG полезные результаты. Код не проверяет качество evidence перед вызовом finalizer'а. Finalizer всегда получает весь собранный evidence и сам решает, что из него использовать.

### Финансовый контекст

Поле `context` в запросе (`AiFinancialContextOptions`) — это **клиентские флаги** о том, какие данные включить. На данный момент backend **не ходит в БД за реальными данными** пользователя (счета, транзакции, активы). Флаги добавляются в системный промпт как строка `"Financial context flags requested by the client: {...}"`. Полноценная подгрузка данных из БД — следующий шаг.

---

## Структура файлов AI-чата

```text
backend/app/
  api/
    routes/ai_chat.py              # 6 эндпоинтов
    router.py                      # регистрация /ai/chat
    dependencies.py                # CurrentUser + DbConnection
  services/
    ai_chat.py                     # оркестрация STT→LLM→TTS
    recommendations/
      orchestrator.py              # planner → tools → finalizer
      ragflow.py                   # RAGFlow-адаптер
      search.py                    # SearXNG-адаптер
      schemas.py                   # строгая planner-схема
      source_policy.py             # фильтрация по allowlist
  schemas/ai_chat.py               # Pydantic-модели (camelCase)
  repositories/ai_chat.py          # доступ к БД
  db/queries/ai_chat.sql           # 9 именованных SQL-запросов
  clients/
    http.py                        # глобальный httpx.AsyncClient
    llm/base.py                    # абстрактный клиент (не исп.)
    llm/openai.py                  # OpenAI-клиент (не исп.)
  prompts/
    llm_text.txt                   # промпт текстового ассистента
    llm_voice.txt                  # промпт голосового ассистента
    stt_system.txt                 # промпт speech-to-text
    tts_system.txt                 # промпт text-to-speech
    recommendation_planner.txt
    recommendation_finalizer.txt
    recommendation_context_policy.txt
    recommendation_safety_policy.txt
  settings.py                      # все переменные окружения

frontend/src/
  app/dashboard/chat/page.tsx       # страница чата (текст + голос)
  lib/api/client.ts                 # Axios с авторизацией
  lib/hooks/use-audio-recorder.ts   # Web Audio запись
  components/chat/voice-button.tsx  # кнопка голосового ввода
  components/chat/voice-visualizer.tsx  # анимированная визуализация

tests/
  test_ai_chat.py                   # 2 интеграционных теста
```
