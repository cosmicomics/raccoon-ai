def get(_rule, model, shifts, _allocations, uuid_func):
    person1 = _rule['params']['person1']
    person2 = _rule['params']['person2']
    number_of_hours = _rule['params']['numberOfHours']

    overlaps = []
    for i in range(0, len(shifts)):
        for j in range(i, len(shifts)):
            overlap = max(0, min(shifts[i]['end'], shifts[j]['end']) - max(shifts[i]['start'], shifts[j]['start']))
            if overlap > 0:
                are_staffed_on_overlapping_shifts = model.NewBoolVar(uuid_func())
                model.AddMultiplicationEquality(are_staffed_on_overlapping_shifts, [_allocations[(shifts[i]['id'], person1)], _allocations[(shifts[j]['id'], person2)]])
                overlaps.append(overlap * are_staffed_on_overlapping_shifts)

    variable = sum(overlaps)

    return {
        'variable': variable,
        'targeted_value': number_of_hours
    }
