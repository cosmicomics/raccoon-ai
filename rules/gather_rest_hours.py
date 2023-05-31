def get(_rule, model, shifts, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']

    rests = []
    for i in range(0, len(shifts)):
        for j in range(i + 1, len(shifts)):

            overlapping_shifts = list(filter(lambda x: shifts[i]['end'] < x['start'] < shifts[j]['start'] or shifts[i]['end'] < x['end'] < shifts[j]['start'], shifts))
            rest_bool_var = model.NewBoolVar(uuid_func())
            model.Add(sum(_allocations[(s['id'], person)] for s in overlapping_shifts) == 0).OnlyEnforceIf(rest_bool_var)
            model.Add(sum(_allocations[(s['id'], person)] for s in overlapping_shifts) > 0).OnlyEnforceIf(rest_bool_var.Not())

            rest_bool_var2 = model.NewBoolVar(uuid_func())
            model.AddMultiplicationEquality(rest_bool_var2, [_allocations[(shifts[i]['id'], person)], _allocations[(shifts[j]['id'], person)]])

            rest_bool_var3 = model.NewBoolVar(uuid_func())
            model.AddMultiplicationEquality(rest_bool_var3, [rest_bool_var, rest_bool_var2])

            rest = shifts[j]['start'] - shifts[i]['end']
            rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
            model.Add(rest_var == rest).OnlyEnforceIf(rest_bool_var3)
            model.Add(rest_var == 0).OnlyEnforceIf(rest_bool_var3.Not())
            rests.append(rest_var)

    max_rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())

    if len(rests) > 0:
        model.AddMaxEquality(max_rest_var, rests)

    variable = max_rest_var

    return {
        'variable': variable,
        'targeted_value': number_of_hours
    }
