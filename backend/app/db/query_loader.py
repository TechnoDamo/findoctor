"""
Загрузчик именованных SQL-запросов из .sql файлов.

Формат .sql файлов:
    -- name: имя_запроса
    -- Однострочный комментарий-описание (опционально)
    SELECT ...
    FROM ...

    -- name: другой_запрос
    INSERT ...

Запросы разделяются строкой, начинающейся с `-- name:`.
Всё, что между `-- name:` и следующим `-- name:` (или концом файла),
считается телом запроса.

Пример использования:
    queries = load_queries("accounts.sql")
    result = conn.execute(queries["list_accounts"], params)
"""

import re
from pathlib import Path

_QUERIES_DIR = Path(__file__).parent / "queries"
_NAME_PATTERN = re.compile(r"^--\s*name:\s*(\S+)")


def load_queries(filename: str) -> dict[str, str]:
    """
    Загружает все именованные SQL-запросы из файла.

    Args:
        filename: Имя .sql файла в директории queries (например, "accounts.sql").

    Returns:
        Словарь {имя_запроса: sql_текст}.
        Имена запросов соответствуют значению после `-- name:` в файле.

    Raises:
        FileNotFoundError: если файл не найден.
        ValueError: если в файле нет ни одного именованного запроса.
    """
    filepath = _QUERIES_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Файл с запросами не найден: {filepath}")

    content = filepath.read_text(encoding="utf-8")
    queries: dict[str, str] = {}

    current_name: str | None = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        match = _NAME_PATTERN.match(line)
        if match:
            if current_name is not None:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = match.group(1)
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        queries[current_name] = "\n".join(current_lines).strip()

    if not queries:
        raise ValueError(f"Файл {filename} не содержит именованных запросов (-- name: ...)")

    return queries
