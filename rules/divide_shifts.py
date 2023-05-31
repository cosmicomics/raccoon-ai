# Divide shifts between a set of persons.
# An interval might be provided : only shifts starting
# in the given period are then taken into account.
# A set of shifts can also be provided as a filter.


def get(_rule, _shifts, model, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    persons = _rule['params']['persons']
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

    average_number_of_shifts_per_person = len(selected_shifts) // len(persons)
    remainder = len(selected_shifts) - average_number_of_shifts_per_person * len(persons)

    distances_from_average = []
    for p in persons:
        slack_pos = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.Add(average_number_of_shifts_per_person - slack_pos + slack_neg == sum(_allocations[(s['id'], p)] for s in selected_shifts))
        distances_from_average.append(slack_pos)
        distances_from_average.append(slack_neg)

    # every shift should be allocated
    slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(len(selected_shifts) * len(selected_shifts) - slack_neg == len(selected_shifts) * sum(_allocations[(s['id'], p)] for s in selected_shifts for p in persons))
    distances_from_average.append(slack_neg)

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, distances_from_average)

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(distances_from_average))

    prod = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddProdEquality(prod, [max_slack, sum_slacks])

    variable = prod

    return {
        'variable': variable,
        'targeted_value': remainder
    }
