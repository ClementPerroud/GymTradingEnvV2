from enders import AbstractEnder

def ender_deep_search(element : object, __list_to_fill : list = [],  __visited : list = [], __include = False):
    if id(element) in __visited : return __list_to_fill
    __visited.append(id(element))

    if isinstance(element, AbstractEnder) and __include:
        __list_to_fill.append(element)
    
    for child_element in get_iterator(element=element):
        ender_deep_search(element= child_element, __list_to_fill= __list_to_fill, __visited= __visited, __include = True)
    return __list_to_fill

def get_iterator(element):
    if isinstance(element, list):
        return element
    if hasattr(element, "__dict__"):
        return element.__dict__.values()
    return []