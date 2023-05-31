# Find a period with no shifts assigned.
# Length and offset of the period are required.
# from_date and to_date are mandatory too.
# slack value refers to number of shifts in plus of zero, on the period

def get(_rule, _shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    period_length = _rule['params']['periodLength']
    period_offset = _rule['params']['periodOffset']
    from_date = _rule['params']['fromDate']
    to_date = _rule['params']['toDate']

    shifts = []
    for s in _shifts:

        is_in_interval = True
        if from_date is not None and to_date is not None:
            is_in_interval = from_date <= s['start'] < to_date

        if is_in_interval:
            shifts.append(_allocations[(s['id'], person)])

    candidate_periods = []
    for date in range(from_date, to_date):
        if date % period_offset == 0:
            candidate_periods.append({
                'start': date,
                'end': date + period_length
            })

    number_of_shifts_in_period_vars = []
    for period in candidate_periods:
        shifts_in_period = list(filter(lambda s: period['start'] < s['start'] < period['end'], shifts))
        period_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
        model.Add(period_var == sum([_allocations[(s['id'], person)] for s in shifts_in_period]))
        number_of_shifts_in_period_vars.append(period_var)

    min_number_of_shifts_in_period_vars = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
    model.AddMinEquality(min_number_of_shifts_in_period_vars, number_of_shifts_in_period_vars)

    return {
        'variable': min_number_of_shifts_in_period_vars,
        'targeted_value': 0
    }
