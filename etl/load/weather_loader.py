#loader meteo
from sqlalchemy import text
def get_or_create_weather(conn, weather):
    row = conn.execute(
        text("""
        SELECT weather_key
        FROM dim_weather
        WHERE airport_icao=:airport
        AND observation_time=:obs
        """),
        {
            "airport": weather["station"],
            "obs": weather["time"]["dt"]
        }
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        text("""
        INSERT INTO dim_weather(
            airport_icao,
            observation_time,
            temperature,
            pressure,
            humidity,
            wind_speed,
            wind_direction,
            visibility,
            metar
        )
        VALUES(
            :airport,
            :obs,
            :temp,
            :pressure,
            :humidity,
            :wind,
            :direction,
            :visibility,
            :metar
        )
        RETURNING weather_key
        """),
        {
            "airport": weather["station"],
            "obs": weather["time"]["dt"],
            "temp": weather["temperature"]["value"],
            "pressure": weather["altimeter"]["value"],
            "humidity": None,
            "wind": weather["wind_speed"]["value"],
            "direction": weather["wind_direction"]["value"],
            "visibility": weather["visibility"]["value"],
            "metar": weather["raw"]
        }
    )
    return row.fetchone()[0]
