\echo Удаляем тестовых пользователей FinDoctor и все зависимые записи...

BEGIN;

CREATE TEMP TABLE scenario_users_to_delete AS
SELECT id
FROM users
WHERE email IN (
    'scenario.alexei.stability@findoctor.test',
    'scenario.irina.freelance@findoctor.test',
    'scenario.pavel.debt-recovery@findoctor.test',
    'scenario.elena.family-mortgage@findoctor.test',
    'scenario.nikolai.retirement@findoctor.test'
);

DELETE FROM ai_chat_messages
WHERE conversation_id IN (
    SELECT id FROM ai_chat_conversations WHERE user_id IN (SELECT id FROM scenario_users_to_delete)
);

DELETE FROM ai_chat_conversations WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM auth_sessions WHERE user_id IN (SELECT id FROM scenario_users_to_delete);

DELETE FROM transaction_tags
WHERE transaction_id IN (
    SELECT id FROM transactions WHERE user_id IN (SELECT id FROM scenario_users_to_delete)
)
OR tag_id IN (
    SELECT id FROM tags WHERE user_id IN (SELECT id FROM scenario_users_to_delete)
);

DELETE FROM liability_payments WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM transactions WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM transfers WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM recurring_transactions WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM daily_financial_snapshots WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM financial_goals WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM tags WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM liabilities WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM assets WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM accounts WHERE user_id IN (SELECT id FROM scenario_users_to_delete);
DELETE FROM users WHERE id IN (SELECT id FROM scenario_users_to_delete);

DROP TABLE scenario_users_to_delete;

DELETE FROM financial_institution_provider_types
WHERE financial_institution_id IN (
    SELECT id FROM financial_institutions WHERE integration_key LIKE 'test_scenario_%'
);

DELETE FROM financial_institutions WHERE integration_key LIKE 'test_scenario_%';
DELETE FROM merchants WHERE id::text LIKE '20000000-0000-0000-0000-0000000002%';

COMMIT;

\echo Тестовые сценарии удалены.
