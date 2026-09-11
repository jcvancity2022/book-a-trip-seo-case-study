"""SQLite data access for Book a Trip.

Demo/portfolio project — payments recorded here are not processed against
any real payment gateway. This just persists a payment record against a
trip booking for the SEO case-study booking flow.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "bookatrip.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                traveler_name TEXT NOT NULL,
                email TEXT NOT NULL,
                destination TEXT NOT NULL,
                trip_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'CAD',
                method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                transaction_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id)
            )
        """)
        # Mirrors the Stage 4 keyword-research template from the SEO course
        # audit. Rows are only ever entered from real tool output -- nothing
        # in this app writes a value here automatically.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS keyword_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                parent_topic TEXT,
                location TEXT,
                search_volume INTEGER,
                volume_source TEXT,
                traffic_potential_notes TEXT,
                business_potential INTEGER CHECK (business_potential BETWEEN 0 AND 3),
                intent TEXT,
                content_type TEXT,
                content_format TEXT,
                content_angle TEXT,
                ranking_difficulty TEXT,
                serp_observations TEXT,
                recommended_action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Mirrors Ahrefs' Content Gap tool exactly, per the course lesson:
        # feed in 2-3 competitor URLs ("targets"), find keywords where at
        # least 2 of them rank and at least 1 ranks in the top 10 (the
        # "2 targets" / "3 targets" intersections filter from the video).
        # Rows are only ever entered from a real tool run against real
        # competitor URLs -- nothing here is generated automatically.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS content_gap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_page TEXT NOT NULL,
                target1_url TEXT,
                target2_url TEXT,
                target3_url TEXT,
                keyword TEXT NOT NULL,
                search_volume INTEGER,
                kd INTEGER,
                cpc REAL,
                target1_position INTEGER,
                target2_position INTEGER,
                target3_position INTEGER,
                intersections TEXT CHECK (intersections IN ('1 target', '2 targets', '3 targets')),
                include_on_page INTEGER CHECK (include_on_page IN (0, 1)),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Mirrors the Ahrefs link-building module's five-attribute scorecard
        # (relevance, authority, anchor text, follow status, placement) and
        # its prospecting -> vetting -> outreach process. Rows are only ever
        # entered from a real page someone actually opened and read -- the
        # authority_status field stays "Needs Ahrefs" rather than a guessed
        # DR/UR number until a live Ahrefs session checks it.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS link_prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_page TEXT NOT NULL,
                prospect_url TEXT NOT NULL,
                domain TEXT,
                channel TEXT CHECK (channel IN ('outreach', 'source', 'organic')),
                relevance_note TEXT,
                authority_status TEXT,
                editorial_placement TEXT,
                links_out INTEGER CHECK (links_out IN (0, 1)),
                verdict TEXT CHECK (verdict IN ('top prospect', 'strong', 'medium', 'skip')),
                status TEXT NOT NULL DEFAULT 'not contacted'
                    CHECK (status IN ('not contacted', 'vetted', 'contacted', 'replied', 'linked', 'declined')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_booking(traveler_name, email, destination, trip_date):
    """Insert a booking row. Returns the new booking id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO bookings (traveler_name, email, destination, trip_date)
            VALUES (?, ?, ?, ?)
            """,
            (traveler_name, email, destination, trip_date),
        )
        return cursor.lastrowid


def get_booking(booking_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()
        return dict(row) if row else None


def record_payment(booking_id, amount, method, currency="CAD",
                    status="pending", transaction_ref=None):
    """Insert a payment row tied to a booking. Returns the new payment id.

    Raises sqlite3.IntegrityError if booking_id does not reference an
    existing booking.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO payments (booking_id, amount, currency, method, status, transaction_ref)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (booking_id, amount, currency, method, status, transaction_ref),
        )
        return cursor.lastrowid


def get_payment(payment_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        return dict(row) if row else None


def get_payments_for_booking(booking_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM payments WHERE booking_id = ? ORDER BY created_at",
            (booking_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_payment_by_transaction_ref(transaction_ref):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM payments WHERE transaction_ref = ?", (transaction_ref,)
        ).fetchone()
        return dict(row) if row else None


def update_payment_status(transaction_ref, status):
    """Update a payment's status by its processor transaction reference."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE payments SET status = ? WHERE transaction_ref = ?",
            (status, transaction_ref),
        )


KEYWORD_FIELDS = [
    "keyword", "parent_topic", "location", "search_volume", "volume_source",
    "traffic_potential_notes", "business_potential", "intent", "content_type",
    "content_format", "content_angle", "ranking_difficulty",
    "serp_observations", "recommended_action",
]


def create_keyword_entry(**fields):
    """Insert one keyword-research row. Returns the new row's id.

    Only pass fields the researcher actually observed or looked up --
    leave the rest out (they'll store as NULL) rather than guessing.
    """
    if not fields.get("keyword"):
        raise ValueError("keyword is required")

    columns = [f for f in KEYWORD_FIELDS if f in fields]
    placeholders = ", ".join("?" for _ in columns)
    values = [fields[c] for c in columns]

    with get_connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO keyword_research ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid


def get_keyword_entries():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM keyword_research ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_keyword_entry(entry_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM keyword_research WHERE id = ?", (entry_id,)
        ).fetchone()
        return dict(row) if row else None


def update_keyword_entry(entry_id, **fields):
    columns = [f for f in KEYWORD_FIELDS if f in fields]
    if not columns:
        return
    assignments = ", ".join(f"{c} = ?" for c in columns)
    values = [fields[c] for c in columns] + [entry_id]

    with get_connection() as conn:
        conn.execute(
            f"UPDATE keyword_research SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )


def delete_keyword_entry(entry_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM keyword_research WHERE id = ?", (entry_id,))


CONTENT_GAP_FIELDS = [
    "project_page", "target1_url", "target2_url", "target3_url", "keyword",
    "search_volume", "kd", "cpc", "target1_position", "target2_position",
    "target3_position", "intersections", "include_on_page", "notes",
]


def create_content_gap_entry(**fields):
    """Insert one Content Gap row. Returns the new row's id.

    Only pass fields actually read off a real Content Gap tool run --
    leave the rest out rather than guessing a position or volume.
    """
    if not fields.get("project_page"):
        raise ValueError("project_page is required")
    if not fields.get("keyword"):
        raise ValueError("keyword is required")

    columns = [f for f in CONTENT_GAP_FIELDS if f in fields]
    placeholders = ", ".join("?" for _ in columns)
    values = [fields[c] for c in columns]

    with get_connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO content_gap ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid


def get_content_gap_entries(project_page=None):
    with get_connection() as conn:
        if project_page:
            rows = conn.execute(
                "SELECT * FROM content_gap WHERE project_page = ? ORDER BY search_volume DESC NULLS LAST, created_at DESC",
                (project_page,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM content_gap ORDER BY project_page, search_volume DESC NULLS LAST"
            ).fetchall()
        return [dict(row) for row in rows]


def get_content_gap_entry(entry_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM content_gap WHERE id = ?", (entry_id,)
        ).fetchone()
        return dict(row) if row else None


def update_content_gap_entry(entry_id, **fields):
    columns = [f for f in CONTENT_GAP_FIELDS if f in fields]
    if not columns:
        return
    assignments = ", ".join(f"{c} = ?" for c in columns)
    values = [fields[c] for c in columns] + [entry_id]

    with get_connection() as conn:
        conn.execute(
            f"UPDATE content_gap SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )


def delete_content_gap_entry(entry_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM content_gap WHERE id = ?", (entry_id,))


LINK_PROSPECT_FIELDS = [
    "project_page", "prospect_url", "domain", "channel", "relevance_note",
    "authority_status", "editorial_placement", "links_out", "verdict",
    "status", "notes",
]


def create_link_prospect(**fields):
    """Insert one link-prospect row. Returns the new row's id.

    Only pass fields actually read off the real page -- leave authority_status
    as "Needs Ahrefs" (or omit it) rather than guessing a DR/UR number.
    """
    if not fields.get("project_page"):
        raise ValueError("project_page is required")
    if not fields.get("prospect_url"):
        raise ValueError("prospect_url is required")

    columns = [f for f in LINK_PROSPECT_FIELDS if f in fields]
    placeholders = ", ".join("?" for _ in columns)
    values = [fields[c] for c in columns]

    with get_connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO link_prospects ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid


def get_link_prospects(project_page=None):
    with get_connection() as conn:
        if project_page:
            rows = conn.execute(
                "SELECT * FROM link_prospects WHERE project_page = ? ORDER BY created_at DESC",
                (project_page,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM link_prospects ORDER BY project_page, created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


def get_link_prospect(entry_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM link_prospects WHERE id = ?", (entry_id,)
        ).fetchone()
        return dict(row) if row else None


def update_link_prospect(entry_id, **fields):
    columns = [f for f in LINK_PROSPECT_FIELDS if f in fields]
    if not columns:
        return
    assignments = ", ".join(f"{c} = ?" for c in columns)
    values = [fields[c] for c in columns] + [entry_id]

    with get_connection() as conn:
        conn.execute(
            f"UPDATE link_prospects SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )


def delete_link_prospect(entry_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM link_prospects WHERE id = ?", (entry_id,))


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
