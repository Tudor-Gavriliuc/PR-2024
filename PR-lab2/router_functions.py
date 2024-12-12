from datetime import datetime

from db_operations import car_exists, execute_query
import os
import json
from io import BytesIO

expected_types = {
    "name": str,
    "price": float,
    "currency": str,
    "km": str,
    "url": str,
    "update_date": datetime,
    "type": str,
    "views": int,
}

bad_request = 400
ok_request = 200

def car_in_dict(car):
    car_dict = {
        "id": car[0],
        "name": car[1],
        "price": float(car[2]),
        "currency": car[3],
        "km": car[4],
        "url": car[5],
        "update_date": car[6].strftime("%Y-%m-%d %H:%M:%S"),
        "type": car[7],
        "views": car[8]
    }
    return car_dict

def formatting_cars_json(cars):
    car_list = []
    for car in cars:
        car_list.append(car_in_dict(car))
    return car_list

def take_updated_fields(car_id, params):    
    fields = []
    values = []
    
    for key, value in params.items():
        if key in expected_types:
            try:
                if expected_types[key] == float:
                    value = float(value)
                elif expected_types[key] == int:
                    value = int(value)
                elif expected_types[key] == datetime:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                
                fields.append(f"{key} = %s")
                values.append(value)
            except ValueError:
                print(f"Invalid value for {key}. Expected type: {expected_types[key].__name__}")
                return [], []

    
    values.append(car_id)
    return fields, values

def post_car(params):
    car_data = {}
    missing_fields = []
    for field, field_type in expected_types.items():
        if field in params:
            try:
                if field_type == float:
                    car_data[field] = float(params[field])
                elif field_type == int:
                    car_data[field] = int(params[field])
                elif field_type == datetime:
                    car_data[field] = datetime.strptime(params[field], "%Y-%m-%dT%H:%M:%S")
                else:
                    car_data[field] = params[field]
            except ValueError:
                return bad_request, f"Invalid value for {field}. Expected type: {field_type.__name__}"
        else:
            missing_fields.append(field)

    if missing_fields:
        return bad_request, f"Missing required fields: {', '.join(missing_fields)}"

    columns = ', '.join(car_data.keys())
    placeholders = ', '.join(['%s'] * len(car_data))
    query = f"INSERT INTO cars ({columns}) VALUES ({placeholders})"
    values = tuple(car_data.values())

    # Execute the query
    result = execute_query(query, values)
    if result is not None and result > 0:
        return ok_request, "Car inserted successfully"
    else:
        return bad_request, "Failed to insert car"
    
def delete_car(car_id):
    result = car_exists(car_id)
    if not result:
        return bad_request, "No such id"

    delete_query = "DELETE FROM cars WHERE id = %s"
    result = execute_query(delete_query, (car_id,))
    
    if result is not None and result > 0:
        return ok_request, f"Car with ID {car_id} deleted successfully"
    else:
        return bad_request, "Something went wrong"


def parse_multipart_form_data(request_data):
    index_start_content = request_data.find('Content-Disposition:')
    right_part = request_data[index_start_content:]
    end_content = right_part.find("----------------------------")
    lines = right_part.splitlines()
    json_files = []
    json_content = ""
    for line in lines:
        if line.startswith("Content-Disposit") or line.startswith("Content-Type") or line.startswith("---------"):
            if json_content != "":
                json_files.append(json_content)
                json_content = ""
            continue
        json_content += line
    
    
    json_files = list(map(json.loads, json_files))
    return json_files

def take_raw_json(request_data):
    lines = request_data.splitlines()
    return json.loads(lines[-1])