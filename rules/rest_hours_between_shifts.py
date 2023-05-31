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

    period_starts = []
    period_shifts = {}
    for i in range(len(selected_shifts)):
        s = selected_shifts[i]

        if s['end'] in period_starts:
            period_shifts[s['end']].append(s)
        else:
            period_starts.append(s['end'])
            period_shifts[s['end']] = [s]

    period_overlapping_shifts = {}
    for p_start in period_starts:
        period_overlapping_shifts[p_start] = []
        for i in range(len(selected_shifts)):
            s = selected_shifts[i]
            overlap = max(0, min(p_start + number_of_hours, s['end']) - max(p_start, s['start']))
            if overlap > 0:
                period_overlapping_shifts[p_start].append(s)

    slacks = []
    for p_start in period_starts:
        if len(period_overlapping_shifts[p_start]) > 0:

            rests_on_period = []
            for shift in period_overlapping_shifts[p_start]:
                rest = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(rest == max(0, shift['start'] - p_start)).OnlyEnforceIf(_allocations[(shift['id'], person)])
                model.Add(rest == number_of_hours).OnlyEnforceIf(_allocations[(shift['id'], person)].Not())
                rests_on_period.append(rest)

            min_rest_on_period = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.AddMinEquality(min_rest_on_period, rests_on_period)

            staffed_on_shift_followed_by_period = model.NewBoolVar(uuid_func())
            model.Add(sum(_allocations[(s['id'], person)] for s in period_shifts[p_start]) == 0).OnlyEnforceIf(staffed_on_shift_followed_by_period.Not())
            model.Add(sum(_allocations[(s['id'], person)] for s in period_shifts[p_start]) > 0).OnlyEnforceIf(staffed_on_shift_followed_by_period)

            slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.Add(min_rest_on_period + slack_neg == number_of_hours).OnlyEnforceIf(staffed_on_shift_followed_by_period)
            # model.Add(slack_neg == 0).OnlyEnforceIf(staffed_on_shift_followed_by_period.Not())
            slacks.append(slack_neg)

    if len(slacks) == 0:
        slacks.append(model.NewConstant(0))

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, slacks)

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(slacks))

    score = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddProdEquality(score, [max_slack, sum_slacks])

    return {
        'variable': max_slack,
        'targeted_value': 0
    }
