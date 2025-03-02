def class_deep_search(condition, element : object, excluded_classes= tuple(), visited = None, result = None, deepth = 0):
    if result is None: result = set([])
    if visited is None: visited = set([])
    
    element_id = id(element)

    if element_id in visited or isinstance(element, excluded_classes):
        return result

    visited.add(element_id)

    # if element_id in excluded or isinstance(element, excluded_classes):
    #     if level > 0: return result

    if condition(element):
        result.add(element)
    
    for child_element in get_iterator(element=element):
        # print( "".join(["\t"]*deepth) + str(element) )
        class_deep_search(condition= condition, element= child_element, result= result, visited= visited, deepth = deepth +1)
    return result

import numbers
import numpy as np
import pandas as pd
def get_iterator(element):
    if isinstance(element, numbers.Number)\
        or isinstance(element, np.ndarray)\
        or isinstance(element, pd.DataFrame)\
        or isinstance(element, pd.Series)\
        or isinstance(element, StopSearch):
        return []
    if isinstance(element, list):
        if len(element)> 1_000: return []
        return element
    if isinstance(element, dict):
        if len(element)> 1_000: return []
        return list(element.keys()) + list(element.values()) # Seaching in bother keys and values
    if hasattr(element, "__dict__"):
        return element.__dict__.values()
    return []

class StopSearch:
    pass