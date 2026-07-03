from datetime import datetime

from sqlalchemy import text

from etl.utils.postgres import engine
from etl.load.dim_loader import (
    get_or_create_aircraft,
    get_or_create_date,
)


class WarehouseLoader:

    def __init__(self):
        self.engine = engine


def insert_aircraft(self, conn, icao24, callsign):

    return get_or_create_aircraft(
        conn,
        icao24,
        callsign
    )

def insert_date(self, conn, dt):

    return get_or_create_date(
        conn,
        dt
    )

def insert_fact(

        self,
        conn,
        aircraft_key,
        date_key,
        state,
        snapshot

):

    conn.execute(

        text("""

        INSERT INTO fact_flights(

            aircraft_key,

            date_key,

            snapshot_time,

            latitude,

            longitude,

            altitude,

            velocity,

            on_ground

        )

        VALUES(

            :aircraft,

            :date,

            :snapshot,

            :lat,

            :lon,

            :alt,

            :vel,

            :ground

        )

        """),

        {

            "aircraft": aircraft_key,

            "date": date_key,

            "snapshot": snapshot,

            "lat": state[6],

            "lon": state[5],

            "alt": state[7],

            "vel": state[9],

            "ground": state[8],

        }

    )

    def process_snapshot(self, snapshot):

        now = datetime.utcnow()

        with self.engine.begin() as conn:

            date_key = self.insert_date(conn, now)

            for state in snapshot["states"]:

                aircraft_key = self.insert_aircraft(

                    conn,

                    state[0],

                    state[1].strip() if state[1] else None

                )

                self.insert_fact(

                    conn,

                    aircraft_key,

                    date_key,

                    state,

                    now

                )