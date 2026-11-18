-- =====================================================================
-- EeSaala Tracker | seed/03_venues.sql
-- IPL 2026 venues with synthetic reference phase averages (priors).
-- Priors are blended with observed 2026 innings by the venue engine.
-- =====================================================================

INSERT INTO venues (venue_id, venue_code, venue_name, city, prior_pp_runs, prior_mid_runs, prior_death_runs, prior_first_inn_total) VALUES
( 1,'CHN','M. Chinnaswamy Stadium','Bengaluru',          58.0, 88.0, 53.0, 199.0),
( 2,'WAN','Wankhede Stadium','Mumbai',                   54.0, 84.0, 50.0, 188.0),
( 3,'CEP','MA Chidambaram Stadium','Chennai',            48.0, 78.0, 46.0, 172.0),
( 4,'EDN','Eden Gardens','Kolkata',                      54.0, 84.0, 50.0, 188.0),
( 5,'ARJ','Arun Jaitley Stadium','Delhi',                56.0, 86.0, 50.0, 192.0),
( 6,'RGI','Rajiv Gandhi International Stadium','Hyderabad', 60.0, 90.0, 53.0, 203.0),
( 7,'NMS','Narendra Modi Stadium','Ahmedabad',           54.0, 86.0, 51.0, 191.0),
( 8,'SMS','Sawai Mansingh Stadium','Jaipur',             52.0, 82.0, 48.0, 182.0),
( 9,'EKA','BRSABV Ekana Cricket Stadium','Lucknow',      48.0, 78.0, 46.0, 172.0),
(10,'MUL','Maharaja Yadavindra Singh PCA Stadium','Mullanpur', 52.0, 82.0, 48.0, 182.0);
