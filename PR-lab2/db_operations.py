import psycopg2

import psycopg2
import psycopg2.extras
from datetime import datetime

dbname = 'my_db'
user = 'my_user'
password = '12345'
host = 'host.docker.internal'
port = 5438

bad_request = 400
ok_request = 200

def get_connection():
    try:
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        if conn is not None:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                return cur.rowcount
            elif query.strip().upper().startswith('SELECT'):
                return cur.fetchall()

    except psycopg2.Error as e:
        print(f"Error executing query: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def create_cars_table():
    query = """
    CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        currency VARCHAR(3) NOT NULL,
        km VARCHAR(50),  -- Use VARCHAR to accommodate values like 'None'
        url TEXT NOT NULL UNIQUE,
        update_date TIMESTAMP NOT NULL,
        type VARCHAR(50) NOT NULL,  -- e.g., 'Vând' for selling
        views INTEGER NOT NULL DEFAULT 0
    );
    """
    execute_query(query)

def insert_car(name, price, currency, km, url, update_date, type, views):
    query = """
    INSERT INTO cars (name, price, currency, km, url, update_date, type, views)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (name, price, currency, km, url, update_date, type, views)
    execute_query(query, params)

def insert_multiple_cars(car_list):
    query = """
    INSERT INTO cars (name, price, currency, km, url, update_date, type, views)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING  -- Avoid duplicate entries
    """
    conn = None
    try:
        conn = get_connection()
        if conn is not None:
            cur = conn.cursor()
            psycopg2.extras.execute_batch(cur, query, car_list)
            conn.commit()
            print(f"Inserted {len(car_list)} cars successfully.")
    except psycopg2.Error as e:
        print(f"Error inserting cars: {e}")
    finally:
        if conn:
            conn.close()

def get_all_cars():
    query = "SELECT * FROM cars;"
    return execute_query(query)

def get_car_by_id(car_id):
    query = "SELECT * FROM cars WHERE id = %s;"
    return execute_query(query, (car_id,))

def car_exists(car_id):
    query = "SELECT 1 FROM cars WHERE id = %s"
    result = execute_query(query, (car_id,))
    print("***Exists***")
    print(result)
    return result

def update_car(fields, values):
    car_id = values[len(values) - 1] 
    result = car_exists(car_id)
    if not result:
        return bad_request, "No such id"
    query = f"UPDATE cars SET {', '.join(fields)} WHERE id = %s"

    try:
        result = execute_query(query, tuple(values))
        print("***Update***")
        print(result)
        if result is not None and result > 0:
            return ok_request, f"Car with ID {car_id} updated successfully"
        else:
            return bad_request, f"Error updating car: {e}"
    except Exception as e:
        return bad_request, f"Error updating car: {e}"

def get_paginated_cars(page, size):
    offset = (page - 1) * size
    query = "SELECT * FROM cars ORDER BY id LIMIT %s OFFSET %s"
    return execute_query(query, (size, offset))
