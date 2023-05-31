"""
Sets a minimum number of rest hours after specific shifts.
"""


def get(_rule, model, shifts, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    shifts_ids = _rule['params']['shifts']
    number_of_hours = _rule['params']['numberOfHours']

    selected_shifts = list(filter(lambda x: x['id'] in shifts_ids, shifts))

    slacks = []

    for s in selected_shifts:
        period_to_check = {'start': s['end'], 'end': s['end'] + number_of_hours}
        p2c_shifts = list(filter(lambda x: min(x['end'], period_to_check['end']) - max(x['start'], period_to_check['start']) > 0, shifts))

        if len(p2c_shifts) > 0:
            rests_from_s = []

            for s2 in p2c_shifts:
                rest = max(0, max(s['start'], s2['start']) - min(s['end'], s2['end']))

                prod = model.NewBoolVar(uuid_func())
                model.AddProdEquality(prod, [_allocations[(s['id'], person)], _allocations[(s2['id'], person)]])

                rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(rest_var == number_of_hours).OnlyEnforceIf(prod.Not())
                model.Add(rest_var == rest).OnlyEnforceIf(prod)
                rests_from_s.append(rest_var)

            min_rest_from_s = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.AddMinEquality(min_rest_from_s, rests_from_s)

            slack_pos = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())

            model.Add(min_rest_from_s >= number_of_hours - slack_neg + slack_pos)

            slacks.append(slack_pos)
            slacks.append(slack_neg)

    # in case there are no slacks
    slacks.append(model.NewConstant(0))

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(slacks))

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, slacks)

    variable = sum_slacks

    return {
        'variable': variable,
        'targeted_value': 0
    }
