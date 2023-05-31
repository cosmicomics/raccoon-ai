def get(_rule, shifts, _allocations):
    person = _rule['params']['person']
    number_of_shifts = _rule['params']['numberOfShifts']
    variable = sum([_allocations[(s['id'], person)] for s in shifts])

    return {
        'variable': variable,
        'targeted_value': number_of_shifts
    }
