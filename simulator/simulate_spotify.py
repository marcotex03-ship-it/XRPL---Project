import hashlib
import random

ARTISTS_DB = {
    "Taylor Swift":    {"chosen_percentage": 0.5, "listeners_in_percentile": 4500},
    "Guns N' Roses":   {"chosen_percentage": 2.0, "listeners_in_percentile": 3100},
    "Justin Bieber":   {"chosen_percentage": 1.0, "listeners_in_percentile": 5400},
    "Bruno Mars":      {"chosen_percentage": 2.0, "listeners_in_percentile": 7000},
    "Depeche Mode":    {"chosen_percentage": 2.5, "listeners_in_percentile": 2200},
    "Arctic Monkeys":  {"chosen_percentage": 1.0, "listeners_in_percentile": 2000},
    "Imagine Dragons": {"chosen_percentage": 1.5, "listeners_in_percentile": 4800},
    "Maroon 5":        {"chosen_percentage": 2.0, "listeners_in_percentile": 4300},
    "The Beatles":     {"chosen_percentage": 1.0, "listeners_in_percentile": 3600},
    "Queen":           {"chosen_percentage": 1.0, "listeners_in_percentile": 4900},
    "Snoop Dogg":      {"chosen_percentage": 2.5, "listeners_in_percentile": 2800},
    "Mia Martini":     {"chosen_percentage": 5.0, "listeners_in_percentile": 900},
    "Pink Floyd":      {"chosen_percentage": 1.5, "listeners_in_percentile": 2700},
    "Adele":           {"chosen_percentage": 1.0, "listeners_in_percentile": 4600},
    "Black Pink":      {"chosen_percentage": 1.5, "listeners_in_percentile": 3400},
    "Amy Winehouse":   {"chosen_percentage": 2.0, "listeners_in_percentile": 2500},
    "Ed Sheeran":      {"chosen_percentage": 1.5, "listeners_in_percentile": 4400},
    "Martin Garrix":   {"chosen_percentage": 3.0, "listeners_in_percentile": 2100},
    "Kate Bush":       {"chosen_percentage": 3.0, "listeners_in_percentile": 1900},
    "DNCE":            {"chosen_percentage": 4.0, "listeners_in_percentile": 1500},
    "Daft Punk":       {"chosen_percentage": 2.0, "listeners_in_percentile": 2900},
    "Nirvana":         {"chosen_percentage": 1.5, "listeners_in_percentile": 3300},
    "Raffaella Carrà": {"chosen_percentage": 5.0, "listeners_in_percentile": 1200},
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