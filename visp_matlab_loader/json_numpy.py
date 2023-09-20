"""
This functions as a JSON encoder and decoder for dictionaries containing numpy arrays.

It can also handle most Python base types, such as strings, integers, floats, etc.
"""
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """
    Encodes numpy arrays to JSON.
    
    can also handle most Python base types, such as strings, integers, floats, etc.
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {"type": str(obj.dtype), "value": obj.tolist()}
        if isinstance(obj, np.generic):
            return {"type": str(obj.dtype), "value": obj.item()}
        return json.JSONEncoder.default(self, obj)


class JsonNumpy:
    """
    Class for saving and loading JSON files containing numpy arrays.
    Python standard types are also supported.
    """
    def __init__(self, filepath):
        self.filepath = filepath

    def write(self, data):
        with open(self.filepath, "w") as f:
            json.dump(data, f, cls=NumpyEncoder)

    def read(self):
        with open(self.filepath, "r") as f:
            data = json.load(f)
        for key in data:
            if (
                isinstance(data[key], dict)
                and "type" in data[key]
                and "value" in data[key]
            ):
                data[key] = np.array(data[key]["value"], dtype=data[key]["type"])
        return data

    @staticmethod
    def verify(data1, data2):
        for key in data1:
            if isinstance(data1[key], np.ndarray) and isinstance(
                data2[key], np.ndarray
            ):
                if not np.array_equal(data1[key], data2[key]):
                    return False
            else:
                if data1[key] != data2[key]:
                    return False
        return True


def main():
    # Initialize the class with the filepath
    jn = JsonNumpy("data.json")

    # Write a dictionary to the JSON file
    data = {
        "variable1": np.array([1, 2, 3, 4, 5]),
        "variable2": np.array([[6, 7, 8], [9, 10, 11]], dtype=np.uint16),
        "variable3": "hello",
        "variable4": 123,
        "variable5": np.array(45.6, dtype=np.float16),
    }
    jn.write(data)

    # Read the data from the JSON file
    read_data = jn.read()
    print(read_data)
    print("Is the same: ", JsonNumpy.verify(data, read_data))


if __name__ == "__main__":
    main()
