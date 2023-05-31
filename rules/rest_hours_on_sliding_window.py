# minimum consecutive rest hours on a period window

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
        p2c_rests = []

        for i in range(0, len(p2c_shifts)):
            for j in range(i+1, len(p2c_shifts)):

                rest_between = max(0, max(p2c_shifts[i]['start'], p2c_shifts[j]['start']) - min(p2c_shifts[i]['end'], p2c_shifts[j]['end']))
                if rest_between > 0:

                    staffed_on_both_shifts = model.NewBoolVar(uuid_func())
                    model.AddProdEquality(staffed_on_both_shifts, [_allocations[(p2c_shifts[i]['id'], person)], _allocations[(p2c_shifts[j]['id'], person)]])

                    in_between_shifts1 = list(filter(lambda x: min(x['end'], p2c_shifts[j]['start']) - max(x['start'], p2c_shifts[i]['end']) > 0, p2c_shifts))
                    not_staffed_on_in_between_shifts1 = model.NewBoolVar(uuid_func())
                    model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts1) == 0).OnlyEnforceIf(not_staffed_on_in_between_shifts1)
                    model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts1) > 0).OnlyEnforceIf(not_staffed_on_in_between_shifts1.Not())

                    prod1 = model.NewBoolVar(uuid_func())
                    model.AddProdEquality(prod1, [staffed_on_both_shifts, not_staffed_on_in_between_shifts1])

                    rest_between_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                    model.Add(rest_between_var == rest_between * prod1)
                    p2c_rests.append(rest_between_var)

        for i in range(0, len(p2c_shifts)):
            rest_before = max(0, p2c_shifts[i]['start'] - p2c['start'])
            if rest_before > 0:

                in_between_shifts2 = list(filter(
                    lambda x: min(x['end'], p2c_shifts[i]['start']) - max(x['start'], p2c['start']) > 0,
                    p2c_shifts))
                not_staffed_on_in_between_shifts2 = model.NewBoolVar(uuid_func())
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts2) == 0).OnlyEnforceIf(
                    not_staffed_on_in_between_shifts2)
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts2) > 0).OnlyEnforceIf(
                    not_staffed_on_in_between_shifts2.Not())

                prod2 = model.NewBoolVar(uuid_func())
                model.AddProdEquality(prod2, [_allocations[(p2c_shifts[i]['id'], person)], not_staffed_on_in_between_shifts2])

                rest_before_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(rest_before_var == rest_before * prod2)
                p2c_rests.append(rest_before_var)

            rest_after = max(0, p2c['end'] - p2c_shifts[i]['end'])
            if rest_after > 0:
                in_between_shifts3 = list(filter(
                    lambda x: min(x['end'], p2c['end']) - max(x['start'], p2c_shifts[i]['end']) > 0,
                    p2c_shifts))
                not_staffed_on_in_between_shifts3 = model.NewBoolVar(uuid_func())
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts3) == 0).OnlyEnforceIf(
                    not_staffed_on_in_between_shifts3)
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts3) > 0).OnlyEnforceIf(
                    not_staffed_on_in_between_shifts3.Not())

                prod3 = model.NewBoolVar(uuid_func())
                model.AddProdEquality(prod3, [_allocations[(p2c_shifts[i]['id'], person)], not_staffed_on_in_between_shifts3])

                rest_after_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(rest_after_var == rest_after * prod3)
                p2c_rests.append(rest_after_var)

        '''for s in p2c_shifts:
            rest = max(0, s['start'] - p2c['start'], p2c['end'] - s['end'])
            if rest > 0:

                other_shifts = list(filter(lambda x: x['id'] is not s['id'], p2c_shifts))
                not_staffed_on_other_shifts = model.NewBoolVar(uuid_func())
                model.Add(sum(_allocations[(s['id'], person)] for s in other_shifts) == 0).OnlyEnforceIf(not_staffed_on_other_shifts)
                model.Add(sum(_allocations[(s['id'], person)] for s in other_shifts) > 0).OnlyEnforceIf(not_staffed_on_other_shifts.Not())

                prod = model.NewBoolVar(uuid_func())
                model.AddProdEquality(prod, [not_staffed_on_other_shifts, _allocations[(s['id'], person)]])

                rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(rest_var == rest * prod)

                p2c_rests.append(rest_var)'''

        if period > 0:
            not_staffed_on_any_shifts = model.NewBoolVar(uuid_func())
            model.Add(sum(_allocations[(s['id'], person)] for s in p2c_shifts) == 0).OnlyEnforceIf(not_staffed_on_any_shifts)
            model.Add(sum(_allocations[(s['id'], person)] for s in p2c_shifts) > 0).OnlyEnforceIf(not_staffed_on_any_shifts.Not())
            rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.Add(rest_var == period * not_staffed_on_any_shifts)

            p2c_rests.append(rest_var)

        else:
            p2c_rests.append(model.NewConstant(0))

        # retain max slack between rest on period and asked rest
        max_rest_on_period_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.AddMaxEquality(max_rest_on_period_var, p2c_rests)

        slack_pos = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())

        model.Add(max_rest_on_period_var - slack_pos + slack_neg >= number_of_hours)
        model.Add(slack_pos == 0)

        slacks.append(slack_pos)
        slacks.append(slack_neg)

        # slacks.append(max_rest_on_period_var)

    sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.Add(sum_slacks == sum(slacks))

    max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMaxEquality(max_slack, slacks)

    variable = sum_slacks

    # min_rest = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    # model.AddMinEquality(min_rest, slacks)

    return {
        'variable': max_slack,
        'targeted_value': 0
    }
