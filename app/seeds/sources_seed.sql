INSERT INTO sources (code, name, base_url, is_active, crawl_interval_min)
VALUES
  ('wanted', 'Wanted', 'https://www.wanted.co.kr', TRUE, 360),
  ('saramin', 'Saramin', 'https://www.saramin.co.kr', TRUE, 360),
  ('remotive', 'Remotive', 'https://remotive.com', TRUE, 360),
  ('moloco_gh', 'Moloco (Greenhouse)', 'https://boards.greenhouse.io/moloco', TRUE, 180),
  ('sendbird_gh', 'Sendbird (Greenhouse)', 'https://boards.greenhouse.io/sendbird', TRUE, 180),
  ('dunamu_gh', 'Dunamu (Greenhouse)', 'https://boards.greenhouse.io/dunamu', TRUE, 180)
ON CONFLICT (code) DO NOTHING;
