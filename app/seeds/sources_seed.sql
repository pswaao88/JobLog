INSERT INTO sources (code, name, base_url, is_active, crawl_interval_min)
VALUES
  ('wanted', 'Wanted', 'https://www.wanted.co.kr', TRUE, 360),
  ('saramin', 'Saramin', 'https://www.saramin.co.kr', TRUE, 360),
  ('remotive', 'Remotive', 'https://remotive.com', TRUE, 360)

ON CONFLICT (code) DO NOTHING;
