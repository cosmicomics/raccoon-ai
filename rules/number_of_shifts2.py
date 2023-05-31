# Number of shifts for a person.
# An interval might be provided : only shifts starting
# in the given period are then taken into account.
# A set of shifts can also be provided as a filter.


def get(_rule, _shifts, _allocations):
    person = _rule['params']['person']
    number_of_shifts = _rule['params']['numberOfShifts']
    from_date = _rule['params']['fromDate'] if 'fromDate' in _rule['params'] else None
    to_date = _rule['params']['toDate'] if 'toDate' in _rule['params'] else None
    shifts = _rule['params']['shifts'] if 'shifts' in _rule['params'] else None

    shifts_in_interval = []
    for s in _shifts:

        is_in_interval = True
        if from_date is not None and to_date is not None:
            is_in_interval = from_date <= s['start'] < to_date

        if shifts is not None:
            is_in_interval = s['id'] in shifts

        if is_in_interval:
            shifts_in_interval.append(_allocations[(s['id'], person)])

    variable = sum(shifts_in_interval)

    return {
        'variable': variable,
        'targeted_value': number_of_shifts
    }
