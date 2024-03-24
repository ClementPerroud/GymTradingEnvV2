def class_deep_search(condition, element : object, list_to_fill, visited, excluded):
    if id(element) in visited : return list_to_fill
    visited.append(id(element))

    if condition(element) and element not in excluded:
        list_to_fill.append(element)
    
    for child_element in get_iterator(element=element):
        class_deep_search(condition= condition, element= child_element, list_to_fill= list_to_fill, visited= visited, excluded = excluded)
    return list_to_fill

def get_iterator(element):
    if isinstance(element, list):
        return element
    if isinstance(element, dict):
        return list(element.keys()) + list(element.values()) # Seaching in bother keys and values
    if hasattr(element, "__dict__"):
        return element.__dict__.values()
    return []