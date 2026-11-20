import hashlib
import random

ARTISTS_DB = {
    "Arctic Monkeys":    {"chosen_percentage": 1.0, "listeners_in_percentile": 2000},
    "Taylor Swift":      {"chosen_percentage": 0.5, "listeners_in_percentile": 4500},
    "The Weeknd":        {"chosen_percentage": 1.0, "listeners_in_percentile": 6000},
    "Billie Eilish":     {"chosen_percentage": 1.0, "listeners_in_percentile": 5200},
    "Bruno Mars":        {"chosen_percentage": 2.0, "listeners_in_percentile": 7000},
    "Sabrina Carpenter": {"chosen_percentage": 2.0, "listeners_in_percentile": 3800},
    "Coldplay":          {"chosen_percentage": 1.5, "listeners_in_percentile": 4800},
    "Bad Bunny":         {"chosen_percentage": 1.0, "listeners_in_percentile": 4200},
    "Drake":             {"chosen_percentage": 1.0, "listeners_in_percentile": 4000},
    "Kendrick Lamar":    {"chosen_percentage": 2.0, "listeners_in_percentile": 3500},
    "Dua Lipa":          {"chosen_percentage": 2.5, "listeners_in_percentile": 3900},
    "SZA":               {"chosen_percentage": 2.0, "listeners_in_percentile": 3100},
    "Ed Sheeran":        {"chosen_percentage": 1.5, "listeners_in_percentile": 4400},
    "Ariana Grande":     {"chosen_percentage": 1.0, "listeners_in_percentile": 4100},
    "Eminem":            {"chosen_percentage": 1.0, "listeners_in_percentile": 3700},
    "Rihanna":           {"chosen_percentage": 1.5, "listeners_in_percentile": 4600},
    "Olivia Rodrigo":    {"chosen_percentage": 3.0, "listeners_in_percentile": 2900},
    "Lana Del Rey":      {"chosen_percentage": 2.0, "listeners_in_percentile": 3200},
    "Travis Scott":      {"chosen_percentage": 2.0, "listeners_in_percentile": 3400},
    "Måneskin":          {"chosen_percentage": 5.0, "listeners_in_percentile": 1800},
}

DEMO_MAX_PERCENTILE = 6.0


def simulate_user_streams(username: str, n_artists: int = 8) -> list[dict]:
    seed = int(hashlib.md5(username.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    chosen = rng.sample(list(ARTISTS_DB.keys()), k=min(n_artists, len(ARTISTS_DB)))
    return [{"name": a, "streams": rng.randint(15, 1200)} for a in chosen]


def compute_top_listener_vector(
    username: str,
    streamed_artists: list[dict],
    max_percentile: float = DEMO_MAX_PERCENTILE,
) -> list[bool]:
    seed = int(hashlib.md5(f"{username}_eligibility".encode()).hexdigest(), 16)
    rng = random.Random(seed)
    return [
        rng.uniform(0.0, max_percentile) <= ARTISTS_DB[entry["name"]]["chosen_percentage"]
        for entry in streamed_artists
    ]
