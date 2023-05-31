def get(_rule, persons, _allocations):
    shift = _rule['params']['shift']
    number_of_persons = _rule['params']['numberOfPersons']
    variable = sum([_allocations[(shift, p['id'])] for p in persons])

    return {
        'variable': variable,
        'targeted_value': number_of_persons
    }
