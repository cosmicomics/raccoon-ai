'''def get(model, shifts, persons, _allocations):
    number_of_persons = 1

    sums = []
    for s in shifts:
        for p in persons:
            model.Add(sum())
            sums.append()

    variable = sum([_allocations[(s['id'], p['id'])] for p in persons for s in shifts])

    return {
        'variable': variable,
        'targeted_value': number_of_persons
    }
'''