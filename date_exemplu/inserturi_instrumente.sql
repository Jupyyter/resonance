-- 50 random instruments, made by genereaza_inserturi.py (seed 2026).
-- One transaction: if any row breaks a rule, none of them is saved.

BEGIN;

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson Flying V, Ocean Blue', 'New Flying V in ocean blue, set up in our workshop before it ships.', 14459.00, 1, 'new', FALSE, 3.4, '2026-07-28 21:25:38+00', ARRAY['pau ferro', 'basswood', 'rosewood'], NULL, ARRAY['vintage', 'single-coil'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson Les Paul Studio, Vintage White', 'New Les Paul Studio in vintage white, set up in our workshop before it ships.', 5069.00, 3, 'new', FALSE, 4.5, '2026-01-28 15:37:38+00', ARRAY['ash', 'ebony'], NULL, ARRAY['humbucker', 'stage'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Baltic Sound Trading'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Paramount PD-220E, Walnut', 'New Paramount PD-220E in walnut, set up in our workshop before it ships.', 5379.00, 15, 'new', FALSE, 2.0, '2025-10-07 13:19:38+00', ARRAY['maple', 'ovangkol', 'spruce'], NULL, ARRAY['travel', 'nylon strings'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha BB434, Ocean Blue', 'New BB434 in ocean blue, set up in our workshop before it ships.', 8709.00, 0, 'new', FALSE, 5.1, '2026-07-17 09:50:38+00', ARRAY['pau ferro', 'alder', 'maple'], NULL, ARRAY['passive', '5-string'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland JD-Xi, Ocean Blue', 'New JD-Xi in ocean blue, set up in our workshop before it ships.', 9179.00, 6, 'new', FALSE, 14.6, '2026-02-17 06:55:38+00', '{}', NULL, ARRAY['synth', 'weighted keys'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player Mustang, Vintage White', 'Second-hand Player Mustang in good playing condition, checked and set up in our workshop.', 3990.00, 1, 'used', FALSE, 3.5, '2026-08-10 16:16:38+00', ARRAY['basswood', 'rosewood'], NULL, ARRAY['single-coil', 'beginner', 'tremolo'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha Rydeen five-piece kit', 'Refurbished Rydeen five-piece kit: repaired and fully checked, with new strings and a fresh setup.', 10310.00, 0, 'refurbished', FALSE, 3.5, '2025-09-24 02:14:38+00', ARRAY['mahogany', 'poplar'], NULL, ARRAY['mesh heads'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha P-225, Black', 'New P-225 in black, set up in our workshop before it ships.', 10109.00, 8, 'new', FALSE, NULL, '2026-02-17 08:24:38+00', '{}', NULL, ARRAY['88 keys', 'compact', 'workstation'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player II Jazz Bass, Sea Foam Green', 'New Player II Jazz Bass in sea foam green, set up in our workshop before it ships.', 7959.00, 10, 'new', TRUE, 4.4, '2025-01-04 01:46:38+00', ARRAY['rosewood', 'ash'], NULL, ARRAY['stage', 'short scale', 'fretless'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Newporter Player, Ocean Blue', 'New Newporter Player in ocean blue, set up in our workshop before it ships.', 5539.00, 2, 'new', FALSE, 2.0, '2026-10-24 06:21:38+00', ARRAY['spruce'], NULL, ARRAY['beginner', 'classical'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Carpathia Music Supply'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Zildjian S Series 20in Ride', 'New S Series 20in Ride, set up in our workshop before it ships.', 12859.00, 7, 'new', FALSE, 19.2, '2025-08-06 10:48:38+00', ARRAY['maple', 'bronze', 'steel'], NULL, ARRAY['hardware included', 'five-piece'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Zildjian'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Paramount PD-220E, Sunburst', 'New Paramount PD-220E in sunburst, set up in our workshop before it ships.', 9219.00, 0, 'new', FALSE, NULL, '2026-10-30 02:49:38+00', ARRAY['spruce', 'rosewood', 'walnut'], NULL, ARRAY['electro-acoustic'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Carpathia Music Supply'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Pearl Export snare', 'Second-hand Export snare in good playing condition, checked and set up in our workshop.', 2150.00, 0, 'used', FALSE, 17.6, '2026-05-24 22:14:38+00', ARRAY['birch', 'mahogany'], NULL, ARRAY['mesh heads', 'five-piece'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Pearl'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland RD-88, Cherry', 'New RD-88 in cherry, set up in our workshop before it ships.', 7609.00, 5, 'new', FALSE, 11.4, '2026-03-28 07:03:38+00', '{}', NULL, ARRAY['synth'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson ES-335, Candy Apple Red', 'New ES-335 in candy apple red, set up in our workshop before it ships.', 15429.00, 12, 'new', FALSE, 2.9, '2025-04-14 21:10:38+00', ARRAY['maple', 'alder', 'rosewood'], NULL, ARRAY['stage', 'hollow body', 'beginner'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha DTX6K2-X', 'New DTX6K2-X, set up in our workshop before it ships.', 1979.00, 1, 'new', FALSE, 5.1, '2025-06-18 20:31:38+00', ARRAY['poplar'], NULL, ARRAY['beginner', 'mesh heads', 'electronic'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson SG Standard Bass, Cherry', 'Refurbished SG Standard Bass: repaired and fully checked, with new strings and a fresh setup.', 2120.00, 0, 'refurbished', FALSE, 5.0, '2026-01-06 03:02:38+00', ARRAY['maple', 'alder'], NULL, ARRAY['active'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha Revstar RSE20, Sea Foam Green', 'Second-hand Revstar RSE20 in good playing condition, checked and set up in our workshop.', 7670.00, 1, 'used', FALSE, NULL, '2024-12-27 03:09:38+00', ARRAY['ebony', 'rosewood'], NULL, ARRAY['hollow body'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson EB Bass, Cherry', 'New EB Bass in cherry, set up in our workshop before it ships.', 8409.00, 5, 'new', FALSE, 3.4, '2026-10-29 12:43:38+00', ARRAY['mahogany', 'pau ferro', 'alder'], NULL, ARRAY['beginner', '5-string'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player II Jazz Bass, Sunburst', 'New Player II Jazz Bass in sunburst, set up in our workshop before it ships.', 1569.00, 1, 'new', FALSE, 4.5, '2026-03-18 16:51:38+00', ARRAY['mahogany', 'alder', 'maple'], NULL, ARRAY['passive', 'fretless', '5-string'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Carpathia Music Supply'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha FS800, Ocean Blue', 'New FS800 in ocean blue, set up in our workshop before it ships.', 12499.00, 15, 'new', FALSE, 1.8, '2026-06-30 09:50:38+00', ARRAY['nato'], NULL, ARRAY['electro-acoustic', 'nylon strings', 'classical'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland TD-17KVX2', 'New TD-17KVX2, set up in our workshop before it ships.', 5229.00, 12, 'new', FALSE, 30.0, '2026-03-15 15:10:38+00', ARRAY['bronze'], NULL, ARRAY['compact'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player Mustang, Olympic White', 'Refurbished Player Mustang: repaired and fully checked, with new strings and a fresh setup.', 7500.00, 1, 'refurbished', FALSE, 3.7, '2025-02-04 15:36:38+00', ARRAY['ebony', 'basswood'], NULL, ARRAY['lightweight'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha JR2, Candy Apple Red', 'New JR2 in candy apple red, set up in our workshop before it ships.', 11479.00, 0, 'new', FALSE, 2.3, '2026-02-21 02:31:38+00', ARRAY['mahogany'], NULL, ARRAY['classical'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player Mustang, Natural', 'Second-hand Player Mustang in good playing condition, checked and set up in our workshop.', 6860.00, 1, 'used', FALSE, 3.4, '2025-12-12 12:32:38+00', ARRAY['mahogany', 'rosewood', 'alder'], NULL, ARRAY['tremolo'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha TRBX174, Walnut', 'New TRBX174 in walnut, set up in our workshop before it ships.', 10009.00, 3, 'new', FALSE, 3.9, '2025-03-08 09:07:38+00', ARRAY['maple'], NULL, ARRAY['stage'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland GO:KEYS 3, Ocean Blue', 'New GO:KEYS 3 in ocean blue, set up in our workshop before it ships.', 3609.00, 8, 'new', FALSE, 5.0, '2026-09-14 18:40:38+00', '{}', NULL, ARRAY['88 keys', 'compact', 'weighted keys'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Player Mustang Bass, Walnut', 'New Player Mustang Bass in walnut, set up in our workshop before it ships.', 10849.00, 2, 'new', FALSE, 5.0, '2025-06-27 03:06:38+00', ARRAY['alder', 'maple', 'mahogany'], NULL, ARRAY['fretless', 'stage', 'active'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Carpathia Music Supply'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Pearl Masters Maple kit', 'New Masters Maple kit, set up in our workshop before it ships.', 1799.00, 7, 'new', FALSE, 4.4, '2025-09-02 13:57:38+00', ARRAY['poplar', 'bronze'], NULL, ARRAY['mesh heads', 'beginner', 'five-piece'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Pearl'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland GO:KEYS 3, Olympic White', 'New GO:KEYS 3 in olympic white, set up in our workshop before it ships.', 13969.00, 7, 'new', FALSE, 15.7, '2026-06-13 16:09:38+00', '{}', NULL, ARRAY['compact', '61 keys'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Pearl Sensitone snare', 'New Sensitone snare, set up in our workshop before it ships.', 4239.00, 1, 'new', FALSE, 11.3, '2026-07-15 22:05:38+00', ARRAY['bronze', 'poplar', 'maple'], NULL, ARRAY['mesh heads', 'hardware included'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Pearl'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson Thunderbird IV, Candy Apple Red', 'New Thunderbird IV in candy apple red, set up in our workshop before it ships.', 7809.00, 8, 'new', FALSE, 4.6, '2026-09-18 17:35:38+00', ARRAY['pau ferro', 'rosewood'], NULL, ARRAY['passive', '5-string', 'fretless'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Baltic Sound Trading'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha LL16, Ocean Blue', 'New LL16 in ocean blue, set up in our workshop before it ships.', 8289.00, 2, 'new', FALSE, 2.4, '2025-02-06 03:06:38+00', ARRAY['maple', 'mahogany'], NULL, ARRAY['solid top'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha TRBX174, Natural', 'Second-hand TRBX174 in good playing condition, checked and set up in our workshop.', 2760.00, 1, 'used', FALSE, NULL, '2026-04-08 15:24:38+00', ARRAY['ash', 'rosewood', 'alder'], NULL, ARRAY['passive'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Paramount PD-220E, Olympic White', 'New Paramount PD-220E in olympic white, set up in our workshop before it ships.', 10099.00, 1, 'new', FALSE, 2.2, '2025-06-11 23:20:38+00', ARRAY['spruce'], NULL, ARRAY['electro-acoustic', 'solid top'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland GO:KEYS 3, Sea Foam Green', 'New GO:KEYS 3 in sea foam green, set up in our workshop before it ships.', 8269.00, 7, 'new', FALSE, 6.5, '2025-07-14 18:44:38+00', '{}', NULL, ARRAY['weighted keys', '88 keys'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha TRBX505, Sea Foam Green', 'New TRBX505 in sea foam green, set up in our workshop before it ships.', 4179.00, 15, 'new', FALSE, 4.9, '2026-01-17 14:45:38+00', ARRAY['pau ferro'], NULL, ARRAY['stage', 'beginner', 'short scale'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland Octapad SPD-30', 'Refurbished Octapad SPD-30: repaired and fully checked, with new strings and a fresh setup.', 3150.00, 1, 'refurbished', FALSE, 8.1, '2026-10-20 15:24:38+00', ARRAY['maple', 'poplar', 'mahogany'], NULL, ARRAY['electronic', 'hardware included', 'mesh heads'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha CG192S, Ocean Blue', 'Second-hand CG192S in good playing condition, checked and set up in our workshop.', 5540.00, 0, 'used', FALSE, 2.5, '2025-10-13 13:03:38+00', ARRAY['mahogany', 'nato'], NULL, ARRAY['nylon strings', 'classical', 'beginner'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Pearl Decade Maple kit', 'New Decade Maple kit, set up in our workshop before it ships.', 10389.00, 15, 'new', FALSE, NULL, '2026-05-20 02:28:38+00', ARRAY['steel', 'birch', 'bronze'], NULL, ARRAY['beginner', 'five-piece'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Pearl'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Gibson EB Bass, Sea Foam Green', 'New EB Bass in sea foam green, set up in our workshop before it ships.', 7989.00, 2, 'new', FALSE, 4.6, '2025-06-10 18:48:38+00', ARRAY['pau ferro', 'rosewood'], NULL, ARRAY['short scale', 'active'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Gibson'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland SPD-SX PRO', 'New SPD-SX PRO, set up in our workshop before it ships.', 12669.00, 6, 'new', FALSE, NULL, '2025-11-22 11:13:38+00', ARRAY['birch', 'mahogany', 'bronze'], NULL, ARRAY['electronic'], (SELECT id FROM instruments_category WHERE name = 'Drums and percussion'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha TRBX174, Olympic White', 'New TRBX174 in olympic white, set up in our workshop before it ships.', 7699.00, 1, 'new', FALSE, NULL, '2026-04-15 18:31:38+00', ARRAY['ash'], NULL, ARRAY['stage'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Fender Newporter Player, Candy Apple Red', 'New Newporter Player in candy apple red, set up in our workshop before it ships.', 13569.00, 5, 'new', FALSE, 2.0, '2024-12-23 09:59:38+00', ARRAY['maple', 'spruce', 'cedar'], NULL, ARRAY['dreadnought', 'solid top', 'beginner'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Fender'), (SELECT id FROM instruments_distributor WHERE name = 'Carpathia Music Supply'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha FS800, Natural', 'New FS800 in natural, set up in our workshop before it ships.', 859.00, 3, 'new', FALSE, 2.2, '2025-08-04 21:54:38+00', ARRAY['nato', 'mahogany', 'walnut'], NULL, ARRAY['electro-acoustic', 'solid top'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha TRBX505, Sunburst', 'Second-hand TRBX505 in good playing condition, checked and set up in our workshop.', 2160.00, 1, 'used', FALSE, 4.5, '2026-08-30 15:29:38+00', ARRAY['pau ferro'], NULL, ARRAY['short scale', 'fretless', 'stage'], (SELECT id FROM instruments_category WHERE name = 'Basses'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland FANTOM-06, Ocean Blue', 'Second-hand FANTOM-06 in good playing condition, checked and set up in our workshop.', 8230.00, 0, 'used', FALSE, NULL, '2025-04-21 03:31:38+00', '{}', NULL, ARRAY['beginner'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), NULL);

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Roland FANTOM-06, Vintage White', 'New FANTOM-06 in vintage white, set up in our workshop before it ships.', 2929.00, 2, 'new', FALSE, NULL, '2026-11-01 05:39:38+00', '{}', NULL, ARRAY['workstation'], (SELECT id FROM instruments_category WHERE name = 'Keyboards and synthesizers'), (SELECT id FROM instruments_brand WHERE name = 'Roland'), (SELECT id FROM instruments_distributor WHERE name = 'Euro Percussion Partners'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha Pacifica 112V, Sea Foam Green', 'New Pacifica 112V in sea foam green, set up in our workshop before it ships.', 4929.00, 4, 'new', FALSE, 3.5, '2025-07-06 22:43:38+00', ARRAY['basswood'], NULL, ARRAY['lightweight'], (SELECT id FROM instruments_category WHERE name = 'Electric guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Adriatic Instruments'));

INSERT INTO instruments_instrument (name, description, price, stock, condition, left_handed, weight_kg, date_added, materials, image, tags, category_id, brand_id, distributor_id)
VALUES ('Yamaha APX600, Vintage White', 'New APX600 in vintage white, set up in our workshop before it ships.', 7209.00, 7, 'new', FALSE, 2.3, '2025-09-02 11:25:38+00', ARRAY['maple', 'ovangkol', 'cedar'], NULL, ARRAY['dreadnought', 'travel'], (SELECT id FROM instruments_category WHERE name = 'Acoustic guitars'), (SELECT id FROM instruments_brand WHERE name = 'Yamaha'), (SELECT id FROM instruments_distributor WHERE name = 'Danube Audio Distribution'));

COMMIT;
