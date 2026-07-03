# Ce fichier va contenir toutes les fonctions de chargement des dimensions
from sqlalchemy import text
from datetime import datetime


#Aircraft
def get_or_create_aircraft(conn, icao24, callsign):

    row = conn.execute(
        text("""
            SELECT aircraft_key
            FROM dim_aircraft
            WHERE icao24=:icao24
        """),
        {"icao24": icao24},
    ).fetchone()

    if row:
        return row[0]

    row = conn.execute(
        text("""
            INSERT INTO dim_aircraft(
                icao24,
                callsign,
                first_seen
            )

            VALUES(
                :icao24,
                :callsign,
                NOW()
            )

            RETURNING aircraft_key
        """),
        {
            "icao24": icao24,
            "callsign": callsign,
        },
    )

    return row.fetchone()[0]




#Date
def get_or_create_date(conn, timestamp):

    d = timestamp.date()

    row = conn.execute(
        text("""
        SELECT date_key
        FROM dim_date
        WHERE full_date=:d
        """),
        {"d": d},
    ).fetchone()

    if row:
        return row[0]

    row = conn.execute(
        text("""
        INSERT INTO dim_date(

            full_date,
            year,
            quarter,
            month,
            month_name,
            week,
            day,
            weekday,
            hour,
            minute,
            is_weekend

        )

        VALUES(

            :full_date,
            :year,
            :quarter,
            :month,
            :month_name,
            :week,
            :day,
            :weekday,
            :hour,
            :minute,
            :weekend

        )

        RETURNING date_key
        """),
        {
            "full_date": d,
            "year": timestamp.year,
            "quarter": (timestamp.month - 1) // 3 + 1,
            "month": timestamp.month,
            "month_name": timestamp.strftime("%B"),
            "week": timestamp.isocalendar().week,
            "day": timestamp.day,
            "weekday": timestamp.strftime("%A"),
            "hour": timestamp.hour,
            "minute": timestamp.minute,
            "weekend": timestamp.weekday() >= 5,
        },
    )

    return row.fetchone()[0]