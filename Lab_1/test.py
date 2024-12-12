def serialize(data):
    if isinstance(data, dict):
        serialized_items = []
        for key, value in data.items():
            serialized_items.append(f"{serialize(key)}:{serialize(value)}")
        return f"D{{{' '.join(serialized_items)}}}"
    
    elif isinstance(data, list):
        serialized_items = [serialize(item) for item in data]
        return f"L[{' '.join(serialized_items)}]"
    
    elif isinstance(data, str):
        return f"str({data})"
    
    elif isinstance(data, int):
        return f"int({data})"
    
    elif isinstance(data, float):
        return f"float({data})"
    
    else:
        raise ValueError(f"Unsupported data type: {type(data)}") 

a = [{"a" : "va"}, {"b" : 20}]

print(serialize(a))