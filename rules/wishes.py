def get(_rule, shifts, _allocations):
    person = _rule['params']['person']
    shift_wishes = _rule['params']['shiftWishes']
    number_of_shifts = _rule['params']['numberOfShifts'] if 'numberOfShifts' in _rule['params'] else len(shift_wishes)

    variable = sum([_allocations[(s['id'], person)] for s in list(filter(lambda x: x['id'] in shift_wishes, shifts))])

    return {
        'variable': variable,
        'targeted_value': number_of_shifts
    }
