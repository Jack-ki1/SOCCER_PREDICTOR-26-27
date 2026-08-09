"""
Ground/venue metadata. Small, static, illustrative — swap for a real
source (or extend from the FPL API's team data, which includes ground
names) once data/fpl_client.py is live against real network access.
"""
from __future__ import annotations

STADIUMS = {
    "ars": {"name": "Emirates Stadium", "city": "London", "capacity": 60704},
    "mci": {"name": "Etihad Stadium", "city": "Manchester", "capacity": 53400},
    "hul": {"name": "MKM Stadium", "city": "Hull", "capacity": 25586},
    "new": {"name": "St James' Park", "city": "Newcastle upon Tyne", "capacity": 52305},
    "bha": {"name": "American Express Stadium", "city": "Falmer", "capacity": 31800},
    "bre": {"name": "Gtech Community Stadium", "city": "London", "capacity": 17250},
    "ful": {"name": "Craven Cottage", "city": "London", "capacity": 29600},
    "nfo": {"name": "City Ground", "city": "Nottingham", "capacity": 30445},
    "eve": {"name": "Hill Dickinson Stadium", "city": "Liverpool", "capacity": 52888},
    "ips": {"name": "Portman Road", "city": "Ipswich", "capacity": 30311},
    "sun": {"name": "Stadium of Light", "city": "Sunderland", "capacity": 48707},
    "cry": {"name": "Selhurst Park", "city": "London", "capacity": 25486},
    "lee": {"name": "Elland Road", "city": "Leeds", "capacity": 37792},
    "che": {"name": "Stamford Bridge", "city": "London", "capacity": 40343},
    "tot": {"name": "Tottenham Hotspur Stadium", "city": "London", "capacity": 62850},
    "avl": {"name": "Villa Park", "city": "Birmingham", "capacity": 42918},
    "liv": {"name": "Anfield", "city": "Liverpool", "capacity": 61276},
    "mun": {"name": "Old Trafford", "city": "Manchester", "capacity": 74310},
    "bou": {"name": "Vitality Stadium", "city": "Bournemouth", "capacity": 11307},
    "cov": {"name": "Coventry Building Society Arena", "city": "Coventry", "capacity": 32609},
}


def get_stadium(team_id: str) -> dict | None:
    return STADIUMS.get(team_id)
