-- name: list_institutions
-- Поиск финансовых организаций с фильтрацией
SELECT
    fi.id, fi.name, fi.country, fi.website_url, fi.logo_url,
    fi.integration_key, fi.risk_level, fi.is_active,
    COALESCE(json_agg(pt.id) FILTER (WHERE pt.id IS NOT NULL), '[]'::json) AS provider_type_ids
FROM financial_institutions fi
LEFT JOIN financial_institution_provider_types fipt ON fi.id = fipt.financial_institution_id
LEFT JOIN provider_types pt ON fipt.provider_type_id = pt.id
WHERE (%(q)s IS NULL OR fi.name ILIKE %(q_like)s)
  AND (%(country)s IS NULL OR fi.country = %(country)s)
  AND (%(provider_type_code)s IS NULL OR pt.code = %(provider_type_code)s)
  AND (%(active_only)s IS NULL OR fi.is_active = %(active_only)s)
GROUP BY fi.id
ORDER BY fi.name;

-- name: find_institution
-- Получение финансовой организации по id
SELECT
    fi.id, fi.name, fi.country, fi.website_url, fi.logo_url,
    fi.integration_key, fi.risk_level, fi.is_active,
    COALESCE(json_agg(pt.id) FILTER (WHERE pt.id IS NOT NULL), '[]'::json) AS provider_type_ids
FROM financial_institutions fi
LEFT JOIN financial_institution_provider_types fipt ON fi.id = fipt.financial_institution_id
LEFT JOIN provider_types pt ON fipt.provider_type_id = pt.id
WHERE fi.id = %(institution_id)s
GROUP BY fi.id;

-- name: insert_institution
-- Создание финансовой организации
INSERT INTO financial_institutions (id, name, country, website_url, logo_url, integration_key, risk_level, is_active)
VALUES (gen_random_uuid(), %(name)s, %(country)s, %(website_url)s, %(logo_url)s, %(integration_key)s, 'unknown', true)
RETURNING id, name, country, website_url, logo_url, integration_key, risk_level, is_active;

-- name: insert_institution_provider_types
-- Привязка типов провайдеров к организации
INSERT INTO financial_institution_provider_types (financial_institution_id, provider_type_id)
VALUES (%(institution_id)s, %(provider_type_id)s)
ON CONFLICT DO NOTHING;

-- name: update_institution
-- Обновление финансовой организации
UPDATE financial_institutions SET
    name = %(name)s,
    country = %(country)s,
    website_url = %(website_url)s,
    logo_url = %(logo_url)s,
    integration_key = %(integration_key)s,
    risk_level = %(risk_level)s,
    is_active = %(is_active)s
WHERE id = %(institution_id)s
RETURNING id, name, country, website_url, logo_url, integration_key, risk_level, is_active;

-- name: delete_institution_provider_types
-- Удаление всех привязок типов провайдеров
DELETE FROM financial_institution_provider_types WHERE financial_institution_id = %(institution_id)s;
