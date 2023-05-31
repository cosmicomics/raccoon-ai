# Minimum rest hours on a period.
# The length of each shift is included in the processed period.
# The two processed periods are, for each shift :
# 1) |__________[shift]|
# 2) |[shift]__________|
# Overlaps issue is not treated

def get(_rule, model, shifts, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    period = _rule['params']['period']

    slacks = []

    for s in shifts:
        period_before = {'start': s['end'] - period, 'end': s['end']}
        period_after = {'start': s['start'], 'end': s['start'] + period}

        # period before

        shifts_on_period_before = list(filter(lambda x: min(x['end'], period_before['end']) - max(x['start'], period_before['start']) > 0, shifts))
        overlaps_before = [{'overlap': min(s2['end'], period_before['end']) - max(s2['start'], period_before['start']), 'var': _allocations[(s2['id'], person)]} for s2 in shifts_on_period_before]

        slack_before = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.Add(number_of_hours <= slack_before + period - sum([overlap['overlap'] * overlap['var'] for overlap in overlaps_before]))

        slacks.append(slack_before)

        # period after

        shifts_on_period_after = list(
            filter(lambda x: min(x['end'], period_after['end']) - max(x['start'], period_after['start']) > 0, shifts))
        overlaps_after = [{'overlap': min(s2['end'], period_after['end']) - max(s2['start'], period_after['start']),
                            'var': _allocations[(s2['id'], person)]} for s2 in shifts_on_period_after]

        slack_after = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.Add(
            number_of_hours <= slack_after + period - sum([overlap['overlap'] * overlap['var'] for overlap in overlaps_after]))

        slacks.append(slack_after)

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, slacks)

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(slacks))

    score = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddProdEquality(score, [max_slack, sum_slacks])

    return {
        'variable': score,
        'targeted_value': 0
    }
