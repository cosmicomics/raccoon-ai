# Number of periods with no shifts assigned.
# Length, offset and number of required blanks periods are required.
# from_date and to_date are mandatory too.
# slack value refers to the number of black periods missing

def get(_rule, _shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    period_length = _rule['params']['periodLength']
    period_offset = _rule['params']['periodOffset']
    numberOfPeriods = _rule['params']['numberOfPeriods']
    from_date = _rule['params']['fromDate']
    to_date = _rule['params']['toDate']

    periods = []
    for date in range(from_date + period_offset, to_date, period_length):
        periods.append({
            'start': date,
            'end': date + period_length
        })

    blank_period_vars = []
    for period in periods:
        shifts_in_period = list(filter(lambda s: min(period['end'], s['end']) - max(period['start'], s['start']) > 0, _shifts))
        if len(shifts_in_period) > 0:
            blank_period_var = model.NewBoolVar(uuid())
            model.Add(sum(_allocations[(s['id'], person)] for s in shifts_in_period) == 0).OnlyEnforceIf(blank_period_var)
            model.Add(sum(_allocations[(s['id'], person)] for s in shifts_in_period) > 0).OnlyEnforceIf(blank_period_var.Not())
            blank_period_vars.append(blank_period_var)
        else:
            blank_period_vars.append(model.NewConstant(1))

    number_of_blank_period_vars = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
    model.Add(number_of_blank_period_vars == sum(blank_period_vars))

    return {
        'variable': number_of_blank_period_vars,
        'targeted_value': numberOfPeriods
    }
