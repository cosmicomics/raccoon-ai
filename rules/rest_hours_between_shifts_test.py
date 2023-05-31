# Minimum rest before and after each shift.
# An interval might be provided as a filter : only shifts starting in the interval are then considered.
# A set of shifts can also be provided as a filter.


def get(_rule, _shifts, _allocations, model, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    from_date = _rule['params']['fromDate'] if 'fromDate' in _rule['params'] else None
    to_date = _rule['params']['toDate'] if 'toDate' in _rule['params'] else None
    shifts = _rule['params']['shifts'] if 'shifts' in _rule['params'] else None

    selected_shifts = []
    for s in _shifts:

        is_selected = True
        if from_date is not None and to_date is not None:
            is_selected = from_date <= s['start'] < to_date

        if shifts is not None:
            is_selected = s['id'] in shifts

        if is_selected:
            selected_shifts.append(s)

    overlap_vars = []
    for i in range(len(selected_shifts)):
        s1 = selected_shifts[i]
        for j in range(i+1, len(selected_shifts)):
            s2 = selected_shifts[j]
            overlap = max(0, min(s1['end'] + number_of_hours, s2['end']) - max(s1['end'], s2['start']))
            if overlap > 0:
                overlap_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(overlap_var == overlap * _allocations[(s2['id'], person)])
                overlap_vars.append(overlap_var)

    max_overlap = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_overlap, overlap_vars)

    sum_overlaps = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_overlaps == sum(overlap_vars))

    score = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddProdEquality(score, [max_overlap, sum_overlaps])

    return {
        'variable': score,
        'targeted_value': 0
    }
