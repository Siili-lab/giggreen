-- GigGreen Seed Data — Demo / Hackathon

-- ── Employers ─────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO employers (id, phone, company_name, contact_name, location, sector)
VALUES
  (1, '+254700111222', 'SunBridge Energy', 'David Kamau', 'Nairobi', 'Solar'),
  (2, '+254700333444', 'GreenRoots Africa', 'Fatuma Hassan', 'Kisumu', 'Urban Farming'),
  (3, '+254700555666', 'CleanCity Initiative', 'James Mwangi', 'Mombasa', 'E-Waste');

-- ── Workers ───────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO workers (id, phone, name, location, bio, availability, green_categories, impact_score, level, level_name)
VALUES
  (1, '+254712345678', 'Amina Wanjiku',  'Nairobi',  'Experienced solar installer with 2 years in Nairobi estates.', 'full-time',  '["Solar","E-Waste"]',                  245, 2, 'Green Sprout'),
  (2, '+254723456789', 'Brian Otieno',   'Kisumu',   'Passionate about urban farming and food security in Nyanza.', 'part-time',  '["Urban Farming","Carbon Scout"]',      87,  1, 'Green Seed'),
  (3, '+254734567890', 'Grace Muthoni',  'Mombasa',  'Community educator focused on waste management in Coast region.', 'full-time', '["Green Construction","Community Educator"]', 512, 3, 'Green Builder'),
  (4, '+254745678901', 'Peter Njoroge',  'Nairobi',  'E-waste technician trained at Jua Kali. Certified recycler.', 'weekends',  '["E-Waste","Battery Swap"]',            164, 2, 'Green Sprout'),
  (5, '+254756789012', 'Mercy Achieng',  'Kisumu',   'Climate data collector and community mobiliser.', 'full-time',  '["Carbon Scout","Climate Data"]',       330, 3, 'Green Builder');

-- ── Gigs ──────────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO gigs (id, employer_id, title, description, category, location, pay_kes, impact_points, duration, status)
VALUES
  (1, 1, 'Solar Panel Installation — Residential', 'Install 2kW solar system for a family home in Kasarani. Must have basic electrical knowledge.', 'Solar',             'Nairobi', 3500, 50, '2 days',  'open'),
  (2, 1, 'E-Waste Collection Drive — Westlands',   'Collect and sort e-waste from 10 drop-off points across Westlands. Transport provided.', 'E-Waste',           'Nairobi', 1800, 20, '1 day',   'open'),
  (3, 2, 'Urban Farm Setup — Kibera',              'Help establish a rooftop vegetable garden for 20 households. Seeds and tools provided.', 'Urban Farming',     'Nairobi', 2200, 15, '3 days',  'open'),
  (4, 2, 'Carbon Data Collection — Kisumu County', 'Survey 50 households on energy usage and transport. Tablets provided. Must speak Dholuo.', 'Carbon Scout',      'Kisumu',  2800, 25, '5 days',  'open'),
  (5, 3, 'Community Green Education — Mathare',    'Run 3 workshops on waste sorting and composting for Mathare youth.', 'Community Educator','Nairobi', 1500, 30, '3 weeks', 'open'),
  (6, 1, 'Solar Maintenance — Industrial Area',    'Routine maintenance on 15 solar panels at a factory. Safety boots required.', 'Solar',             'Nairobi', 4200, 50, '1 day',   'open'),
  (7, 3, 'Battery Swap Technician — CBD',          'Join mobile battery swap pilot for e-boda riders. Training provided.', 'Battery Swap',      'Mombasa', 2000, 20, 'Ongoing', 'open');
