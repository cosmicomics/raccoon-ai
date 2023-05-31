# Number of hours for a person.
# An interval might be provided : overlaps at the start
# and at the end of the given period are then computed for each shift.
# A set of shifts can also be provided as a filter.

def get(_rule, _shifts, _allocations):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    from_date = _rule['params']['fromDate'] if 'fromDate' in _rule['params'] else None
    to_date = _rule['params']['toDate'] if 'toDate' in _rule['params'] else None
    shifts = _rule['params']['shifts'] if 'shifts' in _rule['params'] else None

    shifts_overlaps_with_interval = []
    for s in _shifts:

        overlap_with_interval = s['length']
        if from_date is not None and to_date is not None:
            overlap_with_interval = max(0, min(s['end'], to_date) - max(s['start'], from_date))

        if overlap_with_interval > 0 and (shifts is None or s['id'] in shifts):
            shifts_overlaps_with_interval.append({'overlap': overlap_with_interval, 'allocation': _allocations[(s['id'], person)]})

    variable = sum([s['allocation'] * s['overlap'] for s in shifts_overlaps_with_interval])

    return {
        'variable': variable,
        'targeted_value': number_of_hours
    }
