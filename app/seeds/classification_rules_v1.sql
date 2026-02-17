INSERT INTO classification_rules
(rule_version, category, target_value, keyword, match_type, priority, weight, is_negation, is_active)
VALUES
-- employment: intern convertible
('v1.0.0','employment','intern_convertible','채용연계형','contains',10,0,false,true),
('v1.0.0','employment','intern_convertible','정규직 전환','contains',10,0,false,true),
('v1.0.0','employment','intern_convertible','전환형 인턴','contains',10,0,false,true),

-- employment: intern experience
('v1.0.0','employment','intern_experience','체험형 인턴','contains',20,0,false,true),
('v1.0.0','employment','intern_experience','직무체험','contains',20,0,false,true),
('v1.0.0','employment','intern_experience','현장실습','contains',20,0,false,true),

-- employment: experienced
('v1.0.0','employment','experienced','3년 이상','contains',30,0,false,true),
('v1.0.0','employment','experienced','경력','contains',30,0,false,true),

-- employment: new grad
('v1.0.0','employment','new_grad','신입','contains',40,0,false,true),
('v1.0.0','employment','new_grad','경력무관','contains',40,0,false,true),
('v1.0.0','employment','new_grad','졸업예정','contains',40,0,false,true),

-- role: backend
('v1.0.0','role','backend','백엔드','contains',10,0,false,true),
('v1.0.0','role','backend','backend','contains',10,0,false,true),
('v1.0.0','role','backend','server','contains',10,0,false,true),
('v1.0.0','role','backend','api','contains',10,0,false,true),
('v1.0.0','role','backend','spring','contains',10,0,false,true),
('v1.0.0','role','backend','java','contains',10,0,false,true),
('v1.0.0','role','backend','kotlin','contains',10,0,false,true),
('v1.0.0','role','backend','django','contains',10,0,false,true),
('v1.0.0','role','backend','fastapi','contains',10,0,false,true),
('v1.0.0','role','backend','node','contains',10,0,false,true),
('v1.0.0','role','backend','go','contains',10,0,false,true),

-- exclude
('v1.0.0','exclude','backend','디자이너','contains',5,0,false,true),
('v1.0.0','exclude','backend','마케터','contains',5,0,false,true),

-- score
('v1.0.0','score','new_grad','신입 가능','contains',10,15,false,true),
('v1.0.0','score','new_grad','경력무관','contains',10,10,false,true),
('v1.0.0','score','new_grad','3년 이상','contains',10,-20,false,true)
ON CONFLICT (rule_version, category, target_value, keyword, is_negation) DO NOTHING;
