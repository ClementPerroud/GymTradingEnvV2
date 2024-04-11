def class_deep_search(condition, element : object, list_to_fill, visited, excluded, excluded_classes, level = 0):
    element_id = id(element)

    if element_id in visited:
        return list_to_fill

    visited.append(element_id)

    if  element_id in excluded or isinstance(element, excluded_classes):
        if level > 0: return list_to_fill

    elif condition(element):
        list_to_fill.append(element)
    
    for child_element in get_iterator(element=element):
        class_deep_search(condition= condition, element= child_element, list_to_fill= list_to_fill, visited= visited, excluded = excluded, excluded_classes= excluded_classes, level= level + 1)
    return list_to_fill

import numbers
import numpy as np
import pandas as pd
def get_iterator(element):
    if isinstance(element, numbers.Number)\
        or isinstance(element, np.ndarray)\
        or isinstance(element, pd.DataFrame)\
        or isinstance(element, pd.Series):
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