def get(_rule, model, shifts, _allocations, uuid_func):
    person = _rule['params']['person']

    overlaps = []
    for i in range(0, len(shifts)):
        for j in range(i+1, len(shifts)):
            overlap = max(0, min(shifts[i]['end'], shifts[j]['end']) - max(shifts[i]['start'], shifts[j]['start']))

            if overlap > 0:
                is_staffed_on_both_shifts = model.NewBoolVar(uuid_func())
                model.AddMultiplicationEquality(is_staffed_on_both_shifts, [_allocations[(shifts[i]['id'], person)], _allocations[(shifts[j]['id'], person)]])
                overlaps.append(overlap * is_staffed_on_both_shifts)
                # model.Add(is_staffed_on_both_shifts == 0)

    variable = sum(overlaps)
    # variable = model.NewBoolVar(uuid_func())

    return {
        'variable': variable,
        'targeted_value': 0
    }
