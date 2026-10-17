"""SQLite database helper for storing and querying song lyrics line-by-line."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"

VENOM_LINES = [
    "I got a song filled with shit for the strong-willed",
    "When the world gives you a raw deal",
    "Sets you off 'til you scream, \"Piss off! Screw you!\"",
    "When it talks to you like you don't belong",
    "Or tells you you're in the wrong field",
    "When something's in your mitochondrial",
    "'Cause it latched on to you, like",
    "Knock knock, let the devil in",
    "Manevolent as I've ever been, head is spinnin'",
    "This medicine's screamin', \"L-L-L-Let us in!\"",
    "L-L-L-Like a salad bowl, Edgar Allan Poe",
    "Bedridden, shoulda been dead a long time ago",
    "Liquid Tylenol, gelatins, think my skeleton's meltin'",
    "Wicked, I get all high when I think I've smelled the scent",
    "Of elephant manure hell, I meant Kahlúa",
    "Screw it, to hell with it, I went through hell with accelerants",
    "And blew up my-my-myself again",
    "Volkswagen, tailspin, bucket matches my pale skin",
    "Mayo and went from Hellmann's and being rail thin",
    "Filet-o-Fish, Scribble Jam, Rap Olympics '97 Freaknik",
    "How can I be down? Me and Bizarre in Florida",
    "Proof's room slept on the floor of 'da motel then",
    "Dr. Dre said, \"Hell yeah!\"",
    "And I got his stamp like a postcard, word to Mel-Man",
    "And I know they're gonna hate",
    "But I don't care, I barely can wait",
    "To hit 'em with the snare and the bass",
    "Square in the face, this fuckin' world better prepare to get laced",
    "Because they're gonna taste my",
    "Venom, (I got that) adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )",
    "Venom, (I got that) adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )",
    "I said knock knock, let the devil in",
    "Shotgun p-p-pellets in the felt pen",
    "Cocked, fuck around and catch a hot one",
    "It-it's evident I'm not done",
    "V-Venomous, the thoughts spun",
    "Like a web and you just caught in 'em",
    "Held against your will like a hubcap or mud flap",
    "Beat strangler attack",
    "So this ain't gonna feel like a love tap",
    "Eat painkiller pills, fuck up the track",
    "Like, what's her name's at the wheel? Danica Patrick",
    "Threw the car into reverse at the Indy, a nut crashin'",
    "Into ya, the back of it just mangled steel",
    "My Mustang and the Jeep Wrangler grill",
    "With the front smashed, much as my rear fender, assassin",
    "Slim be a combination of an actual kamikaze and Gandhi (Gandhi)",
    "Translation, I will probably kill us both",
    "When I end up backin' into ya",
    "You ain't gonna be able to tell what the fuck's happenin' to ya",
    "When you're bit with the",
    "Venom, adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )",
    "Venom, (I got that) adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )",
    "I said knock knock, let the devil in",
    "Alien, E-E-Elliott phone home",
    "Ain't no telling when this chokehold",
    "On this game will end, I'm loco",
    "Became a Symbiote, so",
    "My fangs are in your throat, ho",
    "You're snake-bitten with my venom",
    "With the ballpoint pen I'm",
    "Gun cocked, bump stock, double-aught, buckshot",
    "Tire thumper, a garrote, tie a couple knots",
    "Fired up and caught fire, juggernaut",
    "Punk rock, bitch, it's goin' down like Yung Joc",
    "'Cause the Doc put me on like sunblock",
    "Why the fuck not, you only get one shot",
    "Ate shit 'til I can't taste it",
    "Chased it with straight liquor",
    "Then paint thinner, then drank 'til I faint",
    "And awake with a headache",
    "And I take anything in rectangular shape",
    "Then I wait to face the demons I'm bonded to",
    "'Cause they're chasin' me but I'm part of you",
    "So escapin' me is impossible",
    "I latch onto you like a parasite",
    "And I probably ruined your parents' life",
    "And your childhood too",
    "'Cause if I'm the music that y'all grew up on",
    "I'm responsible for you retarded fools",
    "I'm the super villain Dad and Mom was losin' their marbles to",
    "You marvel that? Eddie Brock is you",
    "And I'm the suit, so call me",
    "Venom, (I got that) adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )",
    "Venom, (I got that) adrenaline momentum",
    "And I'm not knowin' when I'm",
    "Ever gonna slow up and I'm",
    "Ready to snap any moment I'm",
    "Thinkin' it's time to go get 'em",
    "They ain't gonna know what hit 'em",
    "(W-W-When they get bit with the )"
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create SQLite tables and seed 'Eminem - Venom' if not already present."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                artist TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lyric_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
                UNIQUE (song_id, line_number)
            )
            """
        )

        existing = conn.execute(
            "SELECT id FROM songs WHERE LOWER(title) = LOWER(?)", ("Venom",)
        ).fetchone()

        if existing is None:
            cursor = conn.execute(
                "INSERT INTO songs (title, artist) VALUES (?, ?)",
                ("Venom", "Eminem"),
            )
            song_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO lyric_lines (song_id, line_number, text) VALUES (?, ?, ?)",
                [(song_id, idx, line) for idx, line in enumerate(VENOM_LINES, start=1)],
            )
            conn.commit()


def get_song_with_lines(query: str) -> Optional[dict]:
    """Look up a song by title or 'artist - title' (case-insensitive) and return its ordered lines."""
    clean = query.strip()
    with get_connection() as conn:
        song = conn.execute(
            """
            SELECT id, title, artist
            FROM songs
            WHERE LOWER(title) = LOWER(?)
               OR LOWER(artist || ' - ' || title) = LOWER(?)
               OR LOWER(title) LIKE '%' || LOWER(?) || '%'
            LIMIT 1
            """,
            (clean, clean, clean),
        ).fetchone()

        if song is None:
            return None

        lines = conn.execute(
            """
            SELECT line_number, text
            FROM lyric_lines
            WHERE song_id = ?
            ORDER BY line_number ASC
            """,
            (song["id"],),
        ).fetchall()

        return {
            "id": song["id"],
            "title": song["title"],
            "artist": song["artist"],
            "total_lines": len(lines),
            "lines": [dict(line) for line in lines],
        }
