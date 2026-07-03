-- ============================================================================
-- 1. TABLES DE STAGING (Données Brutes Normalisées)
-- ============================================================================

CREATE TABLE IF NOT EXISTS STG_AVIATIONSTACK (
    id BIGSERIAL PRIMARY KEY,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    flight_date DATE,
    flight_number VARCHAR(20),
    airline_name VARCHAR(100),
    airline_iata VARCHAR(5),
    aircraft_icao24 VARCHAR(10),
    departure_iata VARCHAR(5),
    arrival_iata VARCHAR(5),
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    departure_delay INTEGER,
    arrival_delay INTEGER,
    status VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS STG_AVWX (
    id SERIAL PRIMARY KEY,
    airport_icao VARCHAR(4),
    observation_time TIMESTAMP,
    temperature DECIMAL(5,2),
    wind_speed_kmh DECIMAL(6,2),
    visibility_km DECIMAL(6,2)
);

-- ============================================================================
-- 2. DIMENSIONS (Référentiels)
-- ============================================================================

CREATE TABLE IF NOT EXISTS DIM_AIRPORTS (
    airport_key SERIAL PRIMARY KEY,
    iata_code VARCHAR(10) UNIQUE,
    icao_code VARCHAR(10),
    airport_name VARCHAR(100),
    city VARCHAR(100),
    country VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS DIM_AIRLINES (
    airline_key SERIAL PRIMARY KEY,
    iata_code VARCHAR(10) UNIQUE,
    icao_code VARCHAR(10),
    airline_name VARCHAR(100),
    country VARCHAR(100)

); 

CREATE TABLE IF NOT EXISTS dim_aircraft (
    aircraft_key SERIAL PRIMARY KEY,
    icao24 VARCHAR(20) UNIQUE NOT NULL,
    callsign VARCHAR(20),
    registration VARCHAR(20),
    model VARCHAR(50),
    manufacturer VARCHAR(50),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_weather (
    weather_key SERIAL PRIMARY KEY,
    airport_icao VARCHAR(10) NOT NULL,
    weather_source VARCHAR(30),
    observation_time TIMESTAMP,
    temperature DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction INTEGER,
    visibility DOUBLE PRECISION,
    cloud_cover VARCHAR(30),
    metar TEXT,
    UNIQUE(airport_icao, observation_time)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key SERIAL PRIMARY KEY,
    full_date DATE UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day INTEGER,
    weekday VARCHAR(20),
    hour INTEGER,
    minute INTEGER,
    is_weekend BOOLEAN,
    season VARCHAR(20),
    is_holiday BOOLEAN
);

-- 1. On nettoie l'ancienne colonne et on ajoute la nouvelle dans l'ancienne table dim_date
ALTER TABLE dim_date DROP COLUMN IF EXISTS day_of_week;
ALTER TABLE dim_date DROP COLUMN IF EXISTS weekday;
ALTER TABLE dim_date ADD COLUMN IF NOT EXISTS weekday_number INTEGER;

-- 2. On relance l'insertion (Copie-colle cette requête dans ton éditeur)
INSERT INTO dim_date (date_key, full_date, day, month, year, quarter, weekday_number, is_weekend, month_name)
SELECT 
    to_char(datum, 'YYYYMMDD')::integer AS date_key,
    datum AS full_date,
    extract(day FROM datum)::integer AS day,
    extract(month FROM datum)::integer AS month,
    extract(year FROM datum)::integer AS year,
    extract(quarter FROM datum)::integer AS quarter,
    extract(isodow FROM datum)::integer AS weekday_number,
    CASE WHEN extract(isodow FROM datum) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend,
    to_char(datum, 'TMMonth') AS month_name
FROM generate_series('2026-01-01'::date, '2030-12-31'::date, '1 day'::interval) datum
ON CONFLICT (date_key) DO NOTHING;
-- ============================================================================
-- 3. TABLE DE FAITS & METRIQUES ML
-- ============================================================================

CREATE TABLE IF NOT EXISTS FACT_FLIGHTS (
    flight_key BIGSERIAL PRIMARY KEY,
    flight_number VARCHAR(20),
    flight_status VARCHAR(30),
    departure_airport_key INT REFERENCES DIM_AIRPORTS(airport_key),
    arrival_airport_key INT REFERENCES DIM_AIRPORTS(airport_key),
    airline_key INT REFERENCES DIM_AIRLINES(airline_key),
    aircraft_key INTEGER REFERENCES dim_aircraft(aircraft_key),
    weather_key INTEGER REFERENCES dim_weather(weather_key),
    date_key INTEGER REFERENCES dim_date(date_key),
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    departure_delay_min INT,
    arrival_delay_min INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    velocity DOUBLE PRECISION,
    on_ground BOOLEAN,
    -- Variables Environnementales (RSE / CO2)
    estimated_co2_kg DECIMAL(10,2),

    -- Métriques de Machine Learning
    predicted_delay_min INT,
    prediction_probability DECIMAL(5,2),
    prediction_model VARCHAR(30),
    prediction_timestamp TIMESTAMP,

    snapshot_time TIMESTAMP    
);


CREATE INDEX idx_fact_date
ON fact_flights(date_key);

CREATE INDEX idx_fact_airline
ON fact_flights(airline_key);

CREATE INDEX idx_fact_aircraft
ON fact_flights(aircraft_key);

CREATE INDEX idx_fact_departure
ON fact_flights(departure_airport_key);

CREATE INDEX idx_fact_arrival
ON fact_flights(arrival_airport_key);

CREATE INDEX idx_fact_weather
ON fact_flights(weather_key);