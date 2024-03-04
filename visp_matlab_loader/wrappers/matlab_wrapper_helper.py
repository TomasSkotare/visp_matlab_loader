import numpy as np 

def ensure_vector(array, vector_type="column"):
    """
    This function ensures that the input array is a vector of the specified type (column or row).
    
    If the input is a 1D array, it reshapes it into a 2D array where one dimension is 1. The reshaping is done in-place, 
    meaning the original array is modified. The function also converts the array to float type.

    Parameters:
    array (array-like): The input array. If it's not a numpy array, it will be converted to one.
    vector_type (str, optional): The type of vector to ensure. Must be either 'column' or 'row'. Defaults to 'column'.

    Returns:
    np.ndarray: The reshaped array.

    Raises:
    ValueError: If vector_type is not 'column' or 'row'.

    Examples:
    >>> ensure_vector([1, 2, 3], 'column')
    array([[1.],
           [2.],
           [3.]])
    >>> ensure_vector([1, 2, 3], 'row')
    array([[1., 2., 3.]])
    """    
    # Convert the input to a numpy array if it's not already
    if not isinstance(array, np.ndarray):
        array = np.array(array)

    # Convert the array to float type
    array = array.astype(float)

    # If the array is a 1D array, reshape it to a column or row vector
    if len(array.shape) == 1:
        if vector_type == "column":
            array = array.reshape((-1, 1))
        elif vector_type == "row":
            array = array.reshape((1, -1))
        else:
            raise ValueError("vector_type must be either 'column' or 'row'")
    return array