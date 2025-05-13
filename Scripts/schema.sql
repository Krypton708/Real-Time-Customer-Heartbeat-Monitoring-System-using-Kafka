CREATE TABLE heartbeats (
    id SERIAL PRIMARY KEY,
    patient_id INT,
    timestamp TIMESTAMP,
    heart_rate INT
);
