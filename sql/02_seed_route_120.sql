-- Seed data for GamanTrack - Route 120 (Colombo Fort - Homagama / Maharagama)
-- and reference NTC fare data

-- Day types
INSERT INTO day_types (code, name_en, name_si, name_ta, sort_order) VALUES
    ('WEEKDAY', 'Weekday', 'පාදය', 'வார நாள்', 1),
    ('SATURDAY', 'Saturday', 'සඳුදා', 'சதுராரி', 2),
    ('SUNDAY', 'Sunday', 'ඉරිදා', 'ஞாயிறு', 3),
    ('HOLIDAY', 'Holiday', 'නිවාඩු දිනය', 'விடுமுறை', 4)
ON CONFLICT DO NOTHING;

-- Bus service types
INSERT INTO bus_service_types (code, name_en, name_si, name_ta, fare_multiplier) VALUES
    ('NORMAL', 'Normal Bus', 'සාමාන්‍ය බස්', 'சாதாரண பேருந்து', 1.00),
    ('EXPRESS', 'Express Bus', 'ප්‍රේක්ෂක බස්', 'விரைவு பேருந்து', 1.50),
    ('SEMI_EXPRESS', 'Semi Express Bus', 'අර්ධ වේග බස්', 'பாதி வேக பேருந்து', 1.25)
ON CONFLICT DO NOTHING;

-- Stops (Colombo region - PostGIS geography points)
INSERT INTO stops (stop_code, name_en, name_si, name_ta, location, address, is_terminal) VALUES
    ('FORT_RAILWAY', 'Fort Railway Station', 'කොළඹ දුම්රිය ස්ථානය', 'கொலombo ரயில் நிலையம்', 'Fort, Colombo', 'Near Fort Railway Station', TRUE),
    ('MARADANA_TECH_JN', 'Maradana Bus Stand', 'මරදන බස් ස්ථානය', 'மரடனா பஸ்', 'Maradana', 'Maradana', FALSE),
    ('KOTA_PELIYARAYAYA', 'Kota-Peliyaraya', 'කොට පෙලියරය', 'கோடா பெலியரயா', 'Kota', 'Kota', FALSE),
    ('HULFTALE', 'Hulftale', 'හුල්ෆ්ටැලේ', 'ஹுல்ஃப்டேலே', 'Hulftale', 'Hulftale', FALSE),
    ('PANNILA', 'Pannila', 'පණ්නිල', 'பன்னிலா', 'Pannila', 'Pannila', FALSE),
    ('HOMAGAMA', 'Homagama', 'හොමගම', 'ஹோமகம', 'Homagama', 'Homagama', FALSE),
    ('MAHARAGAMA', 'Maharagama', 'මහරගම', 'மகரகம', 'Maharagama', 'Maharagama', FALSE)
ON CONFLICT DO NOTHING;

-- Routes
INSERT INTO routes (route_number, name_en, name_si, name_ta, origin_terminal, destination_terminal, total_distance_km, estimated_duration_min) VALUES
    ('120', 'Colombo - Homagama', 'කොළඹ - හොමගම', 'கொலombo - ஹோமகம', 'Fort Railway Station', 'Homagama', 24.50, 180)
ON CONFLICT DO NOTHING;

-- Route stops with sequences (Order of stops along route 120)
INSERT INTO route_stops (route_id, stop_id, sequence_number, distance_from_origin_km, is_timing_point) VALUES
    (1, 1, 1, 0.00, TRUE),
    (1, 2, 2, 2.50, TRUE),
    (1, 3, 3, 5.00, TRUE),
    (1, 4, 4, 7.50, TRUE),
    (1, 5, 5, 10.00, TRUE),
    (1, 6, 6, 14.00, TRUE),
    (1, 7, 7, 18.00, FALSE),
    (1, 8, 8, 24.50, TRUE)
ON CONFLICT DO NOTHING;

-- Fare stages for Route 120 (NTC stage-based)
INSERT INTO fare_stages (route_id, stage_number, stop_id, stage_name_en, cumulative_distance_km) VALUES
    (1, 1, 1, 'Fort', 0.00),
    (1, 2, 2, 'Maradana', 2.50),
    (1, 3, 3, 'Kota', 5.00),
    (1, 4, 4, 'Hulftale', 7.50),
    (1, 5, 5, 'Pannila', 10.00),
    (1, 6, 6, 'Homagama', 14.00),
    (1, 7, 7, 'Maharagama', 18.00)
ON CONFLICT DO NOTHING;

-- NTC Fare Matrix (base fares from stage N to stage M)
INSERT INTO fare_matrix (service_type_id, from_stage, to_stage, base_fare_lkr, effective_from) VALUES
    (1, 1, 2, 31.00, '2024-01-01'),
    (1, 1, 3, 42.00, '2024-01-01'),
    (1, 1, 4, 52.00, '2024-01-01'),
    (1, 1, 5, 62.00, '2024-01-01'),
    (1, 1, 6, 72.00, '2024-01-01'),
    (1, 1, 7, 81.00, '2024-01-01'),
    (1, 2, 3, 11.00, '2024-01-01'),
    (1, 2, 4, 21.00, '2024-01-01'),
    (1, 2, 5, 31.00, '2024-01-01'),
    (1, 2, 6, 41.00, '2024-01-01'),
    (1, 2, 7, 50.00, '2024-01-01'),
    (1, 3, 4, 11.00, '2024-01-01'),
    (1, 3, 5, 22.00, '2024-01-01'),
    (1, 3, 6, 32.00, '2024-01-01'),
    (1, 3, 7, 41.00, '2024-01-01'),
    (1, 4, 5, 9.00, '2024-01-01'),
    (1, 4, 6, 19.00, '2024-01-01'),
    (1, 4, 7, 28.00, '2024-01-01'),
    (1, 5, 6, 9.00, '2024-01-01'),
    (1, 5, 7, 18.00, '2024-01-01'),
    (1, 6, 7, 9.00, '2024-01-01'),
    (2, 1, 2, 46.50, '2024-01-01'),
    (2, 1, 3, 63.00, '2024-01-01'),
    (2, 1, 4, 78.00, '2024-01-01'),
    (2, 1, 5, 93.00, '2024-01-01'),
    (2, 1, 6, 108.00, '2024-01-01'),
    (2, 1, 7, 121.50, '2024-01-01')
ON CONFLICT DO NOTHING;

-- Schedules (trips for Route 120)
INSERT INTO schedules (route_id, service_type_id, day_type_id, trip_number, direction, origin_stop_id, destination_stop_id, departure_time, arrival_time, is_active) VALUES
    (1, 1, 1, '120-001', 'OUTBOUND', 1, 7, '05:30:00', '12:30:00', TRUE),
    (1, 1, 1, '120-002', 'OUTBOUND', 1, 7, '06:30:00', '13:30:00', TRUE),
    (1, 1, 2, '120-001', 'INBOUND', 7, 1, '15:00:00', '22:00:00', TRUE),
    (1, 1, 3, '120-002', 'INBOUND', 7, 1, '16:00:00', '23:00:00', TRUE)
ON CONFLICT DO NOTHING;

-- Admin user (development)
INSERT INTO admin_users (username, email, password_hash, full_name, role) VALUES
    ('admin', 'admin@gamantrack.lk', '$2b$12$KIXQJqJ8V9vZ8o1n5lG0HOe6Y7v3nF8oQ9xR2pL0qW8yN3mZ0vA1b', 'GamanTrack Admin', 'SUPER_ADMIN')
ON CONFLICT DO NOTHING;
