"""
Sets a maximum number of hours per period.
Overlaps issues between allocated shifts are not handled.
"""


def get(_rule, model, shifts, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    period = _rule['params']['period']

    periods_to_check_starts = []
    for s in shifts:
        period_before_start = s['end'] - period
        period_after_start = s['start']
        if period_before_start not in periods_to_check_starts:
            periods_to_check_starts.append(period_before_start)
        if period_after_start not in periods_to_check_starts:
            periods_to_check_starts.append(period_after_start)
    periods_to_check = list(map(lambda x: {'start': x, 'end': x + period}, periods_to_check_starts))

    slacks = []

    for p2c in periods_to_check:
        p2c_shifts = list(filter(lambda x: min(x['end'], p2c['end']) - max(x['start'], p2c['start']) > 0, shifts))
        p2c_hours = []

        for s in p2c_shifts:
            hours = min(s['end'], p2c['end']) - max(s['start'], p2c['start'])

            hours_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.Add(hours_var == hours * _allocations[(s['id'], person)])
            p2c_hours.append(hours_var)

        p2c_total_hours = sum(p2c_hours)

        slack_pos = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())

        model.Add(p2c_total_hours <= number_of_hours - slack_neg + slack_pos)

        slacks.append(slack_pos)
        slacks.append(slack_neg)

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(slacks))

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, slacks)

    variable = sum_slacks

    return {
        'variable': variable,
        'targeted_value': 0
    }
