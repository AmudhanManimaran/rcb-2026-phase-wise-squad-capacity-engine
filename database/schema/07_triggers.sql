-- =====================================================================
-- EeSaala Tracker | 07_triggers.sql
-- Data-integrity triggers.
-- =====================================================================

-- 1. Phase tagging on every delivery (formula 01 enforced in the database)
CREATE OR REPLACE FUNCTION trg_fn_bbb_phase() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.phase := fn_phase_of_over(NEW.over_no);
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_bbb_phase ON rcb_ball_by_ball;
CREATE TRIGGER trg_bbb_phase BEFORE INSERT OR UPDATE OF over_no ON rcb_ball_by_ball
FOR EACH ROW EXECUTE FUNCTION trg_fn_bbb_phase();

-- 2. Squad selection limits: at most 11 batting slots and one impact player
CREATE OR REPLACE FUNCTION trg_fn_selection_limits() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_xi INTEGER; v_impact INTEGER; v_overseas INTEGER;
BEGIN
    SELECT COUNT(*) FILTER (WHERE batting_order IS NOT NULL),
           COUNT(*) FILTER (WHERE is_impact_player),
           COUNT(*) FILTER (WHERE p.is_overseas)
      INTO v_xi, v_impact, v_overseas
      FROM rcb_squad_selections s JOIN rcb_players p ON p.player_id = s.player_id
     WHERE s.match_id = NEW.match_id;
    IF v_xi > 11 THEN RAISE EXCEPTION 'Match % has more than 11 batting slots', NEW.match_id; END IF;
    IF v_impact > 1 THEN RAISE EXCEPTION 'Match % has more than one impact player', NEW.match_id; END IF;
    IF v_overseas > 4 THEN RAISE EXCEPTION 'Match % has more than four overseas players', NEW.match_id; END IF;
    RETURN NULL;
END;
$$;
DROP TRIGGER IF EXISTS trg_selection_limits ON rcb_squad_selections;
CREATE CONSTRAINT TRIGGER trg_selection_limits AFTER INSERT OR UPDATE ON rcb_squad_selections
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_fn_selection_limits();

-- 3. Tracker timestamp
CREATE OR REPLACE FUNCTION trg_fn_touch_tracker() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_tracker_touch ON rcb_live_tracker;
CREATE TRIGGER trg_tracker_touch BEFORE UPDATE ON rcb_live_tracker
FOR EACH ROW EXECUTE FUNCTION trg_fn_touch_tracker();

-- 4. Only one active calibration parameter set
CREATE OR REPLACE FUNCTION trg_fn_single_active_param() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.is_active THEN
        UPDATE rcb_calibration_parameters SET is_active = FALSE
         WHERE is_active AND param_id <> NEW.param_id;
    END IF;
    RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_single_active_param ON rcb_calibration_parameters;
CREATE TRIGGER trg_single_active_param BEFORE INSERT OR UPDATE OF is_active ON rcb_calibration_parameters
FOR EACH ROW EXECUTE FUNCTION trg_fn_single_active_param();
