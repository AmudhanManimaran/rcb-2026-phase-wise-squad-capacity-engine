from datetime import date

from pydantic import BaseModel


class MatchSummary(BaseModel):
    match_id: int
    rcb_match_no: int
    ipl_match_no: int
    match_date: date
    opponent_code: str
    venue_code: str
    status: str
    rcb_batting_first: bool
    is_validation_case: bool
