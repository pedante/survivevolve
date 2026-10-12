"""Second evolving seed policy; initially same strength for fair comparison."""
import random


def act(observation, agent_id, num_actions):
    nearby = sum(observation[y][x][3] for y in range(5, 8) for x in range(5, 8))
    if nearby > 0:
        return random.randint(13, min(20, num_actions - 1))
    return random.randint(1, min(12, num_actions - 1))
