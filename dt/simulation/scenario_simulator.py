from typing import List

from dt.models.twin_state import TwinState
from dt.ingestion.state_deriver import update_state


def run_scenario(
    initial_state: TwinState,
    hours: int = 24
) -> List[TwinState]:
    """
    Run the Digital Twin forward for a given number of hours
    and return the full state history.
    """

    history: List[TwinState] = []
    state = initial_state

    for _ in range(hours):
        history.append(state)
        state = update_state(state)

    return history
