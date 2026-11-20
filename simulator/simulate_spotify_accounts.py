import json
import random

ARTISTS = [
    "Måneskin",
    "The Weeknd",
    "Dua Lipa",
    "Coldplay",
    "Taylor Swift",
    "Kendrick Lamar"
]

def simulate_spotify_accounts(num_users=10, min_streams=20, max_streams=60):
    """
    Generates simulated Spotify accounts with listening history and stream counts.
    Returns a list of dictionaries ready for the main program.
    """
    users = []

    for i in range(1, num_users + 1):
        # Each user gets a favorite artist to make the simulation realistic
        favorite = random.choice(ARTISTS)
        weights = [60 if artist == favorite else 8 for artist in ARTISTS]

        num_streams = random.randint(min_streams, max_streams)
        history = random.choices(ARTISTS, weights=weights, k=num_streams)

        # Aggregated count to make life easier for the "Analysis" team
        streams_per_artist = {}
        for artist in history:
            streams_per_artist[artist] = streams_per_artist.get(artist, 0) + 1

        user = {
            "user_id": f"user_{i:03d}",
            "username": f"music_fan_{i}",
            "xrpl_address": None,  # The blockchain ID will go here
            "total_streams": num_streams,
            "streams_per_artist": streams_per_artist,
            "listening_history": history
        }
        users.append(user)

    return users


def save_to_json(users, filename="spotify_data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    data = simulate_spotify_accounts(num_users=5)
    save_to_json(data)
    print("File spotify_data.json created! Preview of the first user:")
    print(json.dumps(data[0], indent=2, ensure_ascii=False))