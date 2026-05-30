# Архитектура И UML-Сценарии ФинДоктора

Документ описывает высокоуровневую архитектуру, deployment-комбинации и основные sequence flows. Диаграммы написаны в Mermaid, чтобы их можно было смотреть прямо в GitHub/GitLab/Markdown-рендерах.

## Компонентная Карта

Диаграмма соответствует целевой схеме: FastAPI является центральным backend-узлом, а AI/STT/TTS/embeddings могут быть локальными или облачными.

```mermaid
flowchart LR
    user["Пользователь\nWeb / mobile / voice UI"] --> frontend["Next.js frontend"]
    frontend --> api["FastAPI backend\nсерверное приложение"]

    subgraph stt["STT модель"]
        whisper["Локальный Whisper.cpp\nили облачный STT API"]
    end

    subgraph tts["TTS модель"]
        vllmomni["Локальный vLLM-Omni\nили облачный TTS API"]
    end

    subgraph llm["Большая языковая модель"]
        vllm["Локальный vLLM\nили облачный LLM API"]
    end

    subgraph emb["Модель эмбеддингов"]
        tei["Локальный Text Embeddings Inference\nили облачный embeddings API"]
    end

    api --> postgres["PostgreSQL\nреляционная база данных"]
    api --> graylog["Graylog + Elasticsearch + MongoDB\nагрегатор логов"]
    api --> whisper
    api --> vllmomni
    api --> vllm
    api --> ragflow["RAGFlow\nRAG-движок"]
    ragflow --> tei
    api --> searxng["SearXNG\nпоисковый движок"]
    searxng --> allowed["Список разрешенных\nвеб-ресурсов"]
```

## Продуктовая Карта Возможностей

```mermaid
flowchart LR
    core["Core CRUD функционал\nфинансы пользователя: доходы, расходы,\nсчета, имущество, обязательства"] --> debt["Кредитный светофор\nанализ долговой нагрузки\nи возможности нового кредита"]
    core --> diagnosis["Финансовый диагноз\nанализ положения и советы\nдля улучшения"]
    core --> goals["Трекер накоплений\nоценка достижимости целей\nи план накопления"]
    core --> assistant["Доп. функционал\nчат с AI, голосовой режим,\nдоступ ассистента к данным,\nфотографии, действия в приложении,\nумные рекомендации"]

    debt --> debt_now["График и описание доходов,\nкоторые идут на долги сейчас"]
    debt --> debt_ratio["График долговой нагрузки\nотносительно нормы"]
    debt --> debt_tips["Советы по снижению\nдолговой нагрузки"]
    debt --> credit_form["Описание условий кредита\nсумма, срок, ставка,\nтекстовые параметры"]
    credit_form --> credit_after["График долгов после\nнового кредита"]
    credit_form --> credit_ratio_after["Долговая нагрузка после\nнового кредита относительно нормы"]
    credit_form --> credit_decision["Советы о целесообразности\nнового кредита"]

    diagnosis --> readable_state["Понятное описание\nфинансовой ситуации"]
    diagnosis --> readable_tips["Понятные советы\nпо улучшению положения"]

    goals --> goal_form["Постановка финансовой цели"]
    goal_form --> goal_realism["Оценка реалистичности цели"]
    goal_form --> goal_plan["Персональный план накопления"]
    goals --> progress["Трекинг прогресса\nв накоплении"]
```

## Sequence: Регистрация И Работа С Финансовыми Данными

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant F as Next.js frontend
    participant A as FastAPI backend
    participant DB as PostgreSQL

    U->>F: Регистрация / логин
    F->>A: POST /api/v1/auth/register или /login
    A->>DB: users + auth_sessions
    DB-->>A: user + session
    A-->>F: access_token + refresh_token

    U->>F: Создает счет / операцию / цель
    F->>A: Bearer request
    A->>A: decode JWT + проверить session
    A->>DB: INSERT/SELECT WHERE user_id = current_user
    DB-->>A: ресурс пользователя
    A-->>F: JSON response
```

## Sequence: Текстовый AI-Чат С User Data Tool

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant F as Frontend
    participant A as FastAPI AI Chat
    participant P as Planner LLM
    participant T as User Data Tool
    participant DB as PostgreSQL
    participant L as Finalizer LLM

    U->>F: "Можно ли досрочно погасить кредит?"
    F->>A: POST /api/v1/ai/chat/messages
    A->>DB: сохранить user message
    A->>P: strict JSON план инструментов
    P-->>A: needed_tools.user_data
    A->>T: выполнить разрешенные финансовые запросы
    T->>DB: user-scoped analytics queries
    DB-->>T: счета, долги, cash-flow, цели
    T-->>A: структурированный результат
    A->>L: вопрос + результаты инструментов + safety policy
    L-->>A: финальный ответ
    A->>DB: сохранить assistant message
    A-->>F: ответ + tool_results + usage
```

## Sequence: RAG/Search Рекомендация

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant A as FastAPI backend
    participant P as Planner LLM
    participant R as RAGFlow
    participant E as TEI / cloud embeddings
    participant S as SearXNG
    participant W as Allowed web resources
    participant L as Finalizer LLM

    U->>A: Вопрос о продукте/ставке/страховке
    A->>P: Сформировать JSON-план
    P-->>A: rag_requests + search_queries
    A->>R: retrieval по dataset
    R->>E: embeddings / vector search
    E-->>R: векторные результаты
    R-->>A: evidence chunks
    A->>S: search query with site allowlist
    S->>W: только разрешенные домены
    W-->>S: найденные страницы
    S-->>A: search snippets
    A->>L: вопрос + chunks + snippets + policy
    L-->>A: grounded recommendation
```

## Sequence: Голосовой Режим

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant F as Frontend voice UI
    participant A as FastAPI backend
    participant STT as Whisper.cpp или cloud STT
    participant LLM as LLM
    participant TTS as vLLM-Omni или cloud TTS
    participant DB as PostgreSQL

    U->>F: Голосовой вопрос
    F->>A: POST /api/v1/ai/chat/audio
    A->>STT: audio base64 / multipart
    STT-->>A: transcript
    A->>LLM: transcript + financial context
    LLM-->>A: text answer
    opt Пользователь запросил аудиоответ
        A->>TTS: text answer
        TTS-->>A: audio payload
    end
    A->>DB: сохранить user/assistant messages
    A-->>F: transcript + text + optional audio
```

## Sequence: Docker Deployment Core

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Разработчик
    participant M as Root Makefile
    participant C as Docker Compose
    participant PG as PostgreSQL container
    participant B as Backend container
    participant FE as Frontend container

    Dev->>M: make deploy-local-core
    M->>M: init-core
    M->>C: docker compose --profile app up -d --build
    C->>PG: start postgres
    PG-->>C: healthcheck ok
    C->>B: build + start backend
    B->>B: alembic upgrade head если RUN_MIGRATIONS=true
    C->>FE: build + start frontend
    FE-->>Dev: http://localhost:3000
    B-->>Dev: http://localhost:8001/api/v1
```

## Deployment-Комбинации

| Сценарий | LLM | STT | TTS | Embeddings | RAG/Search | Команда |
| --- | --- | --- | --- | --- | --- | --- |
| Core app | отключено/облако по env | облако по env | облако по env | нет | нет | `make deploy-local-core` |
| Local RAG | облако/external | облако/external | облако/external | локальный TEI | RAGFlow + SearXNG локально | `make deploy-local-rag` |
| Fully local AI | локальный vLLM | cloud/local по env | cloud/local по env | локальный TEI | RAGFlow + SearXNG локально | `make deploy-local-ai` |
| Hybrid LLM + local RAG | cloud/external LLM | cloud/external | cloud/external | локальный TEI | RAGFlow + SearXNG локально | `make deploy-hybrid-llm-local-rag` |
| Cloud AI/RAG | cloud/external | cloud/external | cloud/external | cloud/external | managed/internal endpoints | `make deploy-cloud-ai` |
| Full local demo | локальный vLLM | optional local/cloud | optional local/cloud | локальный TEI | RAGFlow + SearXNG + Graylog | `make deploy-full-local` |

## Принцип Безопасности

Frontend никогда не получает ключи RAGFlow, SearXNG, LLM, STT, TTS или embeddings. Все секреты находятся на backend side. Модель может предложить план инструментов, но выполнение остается в backend-коде с user-scoped SQL и allowlist источников.
