CREATE TABLE celebrants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    birthdate DATE NOT NULL,
    shareable_link TEXT UNIQUE NOT NULL
);

CREATE TABLE wishes (
    id SERIAL PRIMARY KEY,
    celebrant_id INT REFERENCES celebrants(id),
    well_wisher_name VARCHAR(100) NOT NULL,
    message TEXT,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
