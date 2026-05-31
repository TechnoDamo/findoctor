# Примеры Recommendation Flow

Эти примеры задают ожидаемое поведение planner для recommendation-запросов ПрофИИта.

Planner всегда возвращает строгий JSON:

```json
{
  "response_text": "string",
  "needed_tools": null
}
```

или:

```json
{
  "response_text": "string",
  "needed_tools": {
    "rag": {"rag_requests": ["string"]},
    "search": {"search_queries": ["string"]}
  }
}
```

## Пример 1: Простое Наблюдение По Бюджету

Пользователь:

```text
Почему у меня в этом месяце выросли расходы?
```

Ожидаемый planner:

```json
{
  "response_text": "Нужно посмотреть ваши операции и категории за месяц.",
  "needed_tools": null
}
```

Примечания:

- текущая реализация получает только client-provided `financial_context`;
- когда появятся backend DB tools, этот сценарий должен запрашивать internal finance tools, а не RAG/search.

## Пример 2: Доступность Нового Кредита

Пользователь:

```text
Могу ли я взять автокредит на 3 года?
```

Ожидаемый planner:

```json
{
  "response_text": "Для ответа нужно сопоставить вашу долговую нагрузку с общими правилами по кредитной нагрузке.",
  "needed_tools": {
    "rag": {
      "rag_requests": [
        "debt burden loan affordability personal finance"
      ]
    },
    "search": {
      "search_queries": [
        "site:cbr.ru debt burden consumer loan"
      ]
    }
  }
}
```

Финальный ответ должен явно назвать assumptions:

- стабильность дохода;
- текущие платежи по долгам;
- размер emergency reserve;
- ежемесячные расходы на владение автомобилем;
- факторы, которые изменят рекомендацию.

## Пример 3: Актуальная Ставка, Закон Или Налог

Пользователь:

```text
Какая сейчас ключевая ставка и как она влияет на ипотеку?
```

Ожидаемый planner:

```json
{
  "response_text": "Нужно проверить актуальную информацию из разрешенных источников.",
  "needed_tools": {
    "rag": {
      "rag_requests": [
        "current key rate mortgage impact"
      ]
    },
    "search": {
      "search_queries": [
        "site:cbr.ru ключевая ставка ипотека"
      ]
    }
  }
}
```

Финальный ответ должен ссылаться только на retrieved evidence и избегать устаревших утверждений, если evidence отсутствует.

## Пример 4: Уже Проиндексированные Знания

Пользователь:

```text
Какой размер финансовой подушки мне лучше держать?
```

Ожидаемый planner:

```json
{
  "response_text": "Проверю внутренние материалы по финансовой подушке.",
  "needed_tools": {
    "rag": {
      "rag_requests": [
        "emergency fund size personal finance recommendation"
      ]
    },
    "search": null
  }
}
```

Финальный ответ должен объединить контекст пользователя и retrieved guidance. Если income/expenses отсутствуют, ответ должен быть условным.

## Пример 5: Retrieval Не Нужен

Пользователь:

```text
Что такое кэшфлоу простыми словами?
```

Ожидаемый planner:

```json
{
  "response_text": "Кэшфлоу — это разница между деньгами, которые приходят, и деньгами, которые уходят за период.",
  "needed_tools": null
}
```

## Стиль Финального Ответа

Рекомендуемая структура:

```text
Короткий вывод.

Почему:
- факт из личного контекста;
- факт из evidence;
- ключевое допущение.

Что сделать дальше:
- действие 1;
- действие 2.
```

Для voice mode ответ должен быть короче и без Markdown.

