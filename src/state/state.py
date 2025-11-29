# src/state/state.py

from typing import TypedDict, List, Optional, Dict

class State(TypedDict, total=False):
    messages: List[Dict]
    requirement: str
    breakdown: Dict
    components: Dict
    files: List[Dict]
    package_zip: bytes
    deploy_status: Dict
