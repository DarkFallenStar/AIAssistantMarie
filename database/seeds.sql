-- ====================================================================
-- SEED DATA INICIAL PARA VALIDACIÓN DEL MVP (REQUISITO 8)
-- ====================================================================

-- 1. Usuario de prueba
INSERT INTO users (id, email, full_name, phone_number, preferences)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'usuario@ejemplo.com',
    'Usuario Demo MVP',
    '+573001234567',
    '{"language": "es", "currency": "COP", "notifications": true}'
) ON CONFLICT (id) DO NOTHING;

-- 2. Tareas de prueba (Mínimo 3 tareas)
INSERT INTO tasks (id, user_id, title, description, status, priority, category, due_date)
VALUES 
(
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Revisar presupuesto mensual',
    'Analizar los gastos de la semana con el Asistente Financiero',
    'pending',
    'high',
    'finanzas',
    NOW() + INTERVAL '1 day'
),
(
    'b0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'Entregar informe de avance de tesis',
    'Enviar borrador del capítulo metodológico al director de tesis',
    'pending',
    'high',
    'academico',
    NOW() + INTERVAL '2 days'
),
(
    'b0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'Comprar víveres y café para la semana',
    'Pasar al supermercado al salir del trabajo',
    'pending',
    'medium',
    'hogar',
    NOW() + INTERVAL '3 days'
) ON CONFLICT (id) DO NOTHING;

-- 3. Correos simulados de prueba (Mínimo 3 correos)
INSERT INTO emails (id, user_id, sender, recipient, subject, snippet, status, category, is_important)
VALUES 
(
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'director@universidad.edu',
    'usuario@ejemplo.com',
    'Revisión de Avance de Tesis',
    'Estimado estudiante, por favor confirma la entrega del capítulo 3 para este viernes.',
    'unread',
    'work',
    TRUE
),
(
    'c0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'alertas@bancolombia.com',
    'usuario@ejemplo.com',
    'Notificación de Transferencia Recibida',
    'Has recibido una transferencia por $1.500.000 COP en tu cuenta de ahorros.',
    'unread',
    'finance',
    TRUE
),
(
    'c0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'soporte@empresa.com',
    'usuario@ejemplo.com',
    'Confirmación de Reunión de Planeación',
    'La sesión técnica de planeación del sprint ha sido programada para el lunes a las 10:00 a.m.',
    'read',
    'work',
    FALSE
) ON CONFLICT (id) DO NOTHING;

-- 4. Cuenta bancaria de prueba en COP
INSERT INTO financial_accounts (id, user_id, account_name, account_type, institution, account_number_mask, balance, currency)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Cuenta de Ahorros Principal',
    'savings',
    'Bancolombia',
    '**** 1234',
    3500000.00,
    'COP'
) ON CONFLICT (id) DO NOTHING;

-- 5. Tarjeta de crédito de prueba
INSERT INTO credit_cards (id, user_id, card_name, institution, card_number_mask, credit_limit, current_balance, cutoff_day, due_day)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Tarjeta Clásica',
    'Bancolombia',
    '**** 5678',
    4000000.00,
    450000.00,
    15,
    5
) ON CONFLICT (id) DO NOTHING;

-- 6. Meta de ahorro de prueba
INSERT INTO saving_goals (id, user_id, goal_name, target_amount, current_amount, currency, deadline)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Fondo de Emergencia',
    10000000.00,
    3500000.00,
    'COP',
    '2026-12-31'
) ON CONFLICT (id) DO NOTHING;

-- 7. 10 Transacciones de prueba en COP (5 categorías: alimentación, transporte, educación, ocio, servicios)
INSERT INTO transactions (id, user_id, account_id, type, amount, currency, category, description, merchant, source)
VALUES 
-- Alimentación (2)
(
    '10000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    85000.00,
    'COP',
    'alimentacion',
    'Compra de despensa semanal en supermercado',
    'Supermercado Éxito',
    'manual'
),
(
    '10000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    32000.00,
    'COP',
    'alimentacion',
    'Almuerzo ejecutivo en restaurante',
    'Restaurante Central',
    'manual'
),
-- Transporte (2)
(
    '10000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    45000.00,
    'COP',
    'transporte',
    'Tanqueo de gasolina en estación de servicio',
    'Estación Terpel',
    'manual'
),
(
    '10000000-0000-0000-0000-000000000004',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    18500.00,
    'COP',
    'transporte',
    'Viaje en taxi hacia la oficina',
    'Taxi Urbano',
    'manual'
),
-- Educación (2)
(
    '10000000-0000-0000-0000-000000000005',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    120000.00,
    'COP',
    'educacion',
    'Pago de curso online y certificación técnica',
    'Plataforma Educativa',
    'manual'
),
(
    '10000000-0000-0000-0000-000000000006',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    45000.00,
    'COP',
    'educacion',
    'Compra de libros y materiales de estudio',
    'Librería Nacional',
    'manual'
),
-- Ocio (2)
(
    '10000000-0000-0000-0000-000000000007',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    55000.00,
    'COP',
    'ocio',
    'Entradas de cine y combo de alimentos',
    'Cine Colombia',
    'manual'
),
(
    '10000000-0000-0000-0000-000000000008',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    28000.00,
    'COP',
    'ocio',
    'Suscripción mensual de entretenimiento',
    'Streaming Plus',
    'manual'
),
-- Servicios (2)
(
    '10000000-0000-0000-0000-000000000009',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    95000.00,
    'COP',
    'servicios',
    'Factura de servicio de energía eléctrica',
    'Empresa de Energía',
    'manual'
),
(
    '10000000-0000-0000-0000-000000000010',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'expense',
    75000.00,
    'COP',
    'servicios',
    'Pago de plan de internet de fibra óptica',
    'Claro Hogar',
    'manual'
),
-- Ingreso adicional para balance positivo
(
    '10000000-0000-0000-0000-000000000011',
    'a0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    'income',
    2500000.00,
    'COP',
    'ingreso',
    'Transferencia Recibida (Nómina quincenal)',
    'Empresa Empleadora',
    'manual'
)
ON CONFLICT (id) DO NOTHING;
