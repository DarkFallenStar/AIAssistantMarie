-- ====================================================================
-- SEED DATA INICIAL PARA PRUEBAS (FASE 3)
-- ====================================================================

-- 1. Usuario de prueba
INSERT INTO users (id, email, full_name, phone_number, preferences)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'usuario@ejemplo.com',
    'Usuario Demo',
    '+5215555555555',
    '{"language": "es", "currency": "USD", "notifications": true}'
) ON CONFLICT (id) DO NOTHING;

-- 2. Tarea de prueba
INSERT INTO tasks (id, user_id, title, description, status, priority, category, due_date)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Revisar presupuesto mensual',
    'Analizar los gastos de la semana con el Asistente Financiero',
    'pending',
    'high',
    'finanzas',
    NOW() + INTERVAL '1 day'
) ON CONFLICT (id) DO NOTHING;

-- 3. Correo de prueba
INSERT INTO emails (id, user_id, sender, recipient, subject, snippet, status, category, is_important)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'alertas@banco.com',
    'usuario@ejemplo.com',
    'Compra aprobada por $45.00 en Supermercado',
    'Su tarjeta terminación 5678 registró una compra por $45.00',
    'unread',
    'finance',
    TRUE
) ON CONFLICT (id) DO NOTHING;

-- 4. Cuenta bancaria de prueba
INSERT INTO financial_accounts (id, user_id, account_name, account_type, institution, account_number_mask, balance, currency)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Cuenta Corriente Principal',
    'checking',
    'BBVA',
    '**** 1234',
    2450.75,
    'USD'
) ON CONFLICT (id) DO NOTHING;

-- 5. Tarjeta de crédito de prueba
INSERT INTO credit_cards (id, user_id, card_name, institution, card_number_mask, credit_limit, current_balance, cutoff_day, due_day)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Tarjeta Oro',
    'BBVA',
    '**** 5678',
    3000.00,
    450.25,
    15,
    5
) ON CONFLICT (id) DO NOTHING;

-- 6. Préstamo de prueba
INSERT INTO loans (id, user_id, lender_name, loan_type, original_amount, remaining_balance, interest_rate_annual, monthly_payment, payment_day, start_date)
VALUES (
    'f0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Crédito Automotriz',
    'auto',
    12000.00,
    7800.00,
    11.50,
    320.00,
    20,
    '2025-01-15'
) ON CONFLICT (id) DO NOTHING;

-- 7. Meta de ahorro de prueba
INSERT INTO saving_goals (id, user_id, goal_name, target_amount, current_amount, currency, deadline)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Fondo de Emergencia',
    5000.00,
    1800.00,
    'USD',
    '2026-12-31'
) ON CONFLICT (id) DO NOTHING;

-- 8. Transacción de prueba
INSERT INTO transactions (id, user_id, account_id, type, amount, currency, category, description, merchant, source)
VALUES (
    '10000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    45.00,
    'USD',
    'supermercado',
    'Compra de despensa semanal',
    'Walmart Supercenter',
    'manual'
) ON CONFLICT (id) DO NOTHING;
