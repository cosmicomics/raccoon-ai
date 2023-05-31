# Minimum rest on a period.
# Parameters from_date and to_date are mandatory.
# Parameter "shifts" might be used as a filter.
# The overlap issue is not treated.


def get(_rule, _shifts, _allocations, model, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    from_date = _rule['params']['fromDate']
    to_date = _rule['params']['toDate']
    shifts = _rule['params']['shifts'] if 'shifts' in _rule['params'] else None

    selected_shifts = []
    for s in _shifts:
        if shifts is None or s['id'] in shifts:
            selected_shifts.append(s)

    overlaps = []
    for s in selected_shifts:
        overlap = max(0, min(s['end'], to_date) - max(s['start'], from_date))
        if overlap > 0:
            overlaps.append({'overlap': overlap, 'allocation': _allocations[(s['id'], person)]})

    rest = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(rest == to_date - from_date - sum([x['overlap'] * x['allocation'] for x in overlaps]))

    return {
        'variable': rest,
        'targeted_value': number_of_hours
    }
