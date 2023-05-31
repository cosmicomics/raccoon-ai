def get(_rule, shifts, _allocations):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    variable = sum([_allocations[(s['id'], person)] * s['length'] for s in shifts])

    return {
        'variable': variable,
        'targeted_value': number_of_hours
    }
