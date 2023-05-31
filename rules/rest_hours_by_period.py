def get(_rule, model, shifts, _allocations, uuid_func, INT_VAR_MIN, INT_VAR_MAX):
    person = _rule['params']['person']
    number_of_hours = _rule['params']['numberOfHours']
    period = _rule['params']['period']

    first_period = min(s['start'] for s in shifts) // period
    last_period = max(s['end'] for s in shifts) // period

    slacks = []

    for i in range(first_period, last_period):
        period_start = period * i
        period_end = period * (i + 1)
        shifts_on_period = list(filter(lambda x: min(period_end,  x['end']) - max(period_start, x['start']) > 0, shifts))

        rests_on_period = []

        # inter-shifts rests
        for s1 in range(0, len(shifts_on_period) - 1):
            for s2 in range(s1 + 1, len(shifts_on_period)):
                rest = max(shifts_on_period[s1]['start'], shifts_on_period[s2]['start']) - min(shifts_on_period[s1]['end'], shifts_on_period[s2]['end'])

                if rest > 0:
                    in_between_shifts = list(filter(lambda x: min(shifts_on_period[s1]['end'], shifts_on_period[s2]['end']) <= x['start'] <= max(shifts_on_period[s1]['start'], shifts_on_period[s2]['start']) or min(shifts_on_period[s1]['end'], shifts_on_period[s2]['end']) <= x['end'] <= max(shifts_on_period[s1]['start'], shifts_on_period[s2]['start']), shifts_on_period))
                    not_staffed_on_in_between_shifts = model.NewBoolVar(uuid_func())
                    model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) == 0).OnlyEnforceIf(not_staffed_on_in_between_shifts)
                    model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) > 0).OnlyEnforceIf(not_staffed_on_in_between_shifts.Not())

                    staffed_on_both_shifts = model.NewBoolVar(uuid_func())
                    model.AddMultiplicationEquality(staffed_on_both_shifts, [_allocations[(shifts_on_period[s1]['id'], person)], _allocations[(shifts_on_period[s2]['id'], person)]])

                    staffed_on_both_shifts_with_length = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                    model.Add(staffed_on_both_shifts_with_length == rest * staffed_on_both_shifts)

                    rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                    model.AddMultiplicationEquality(rest_var, [staffed_on_both_shifts, not_staffed_on_in_between_shifts])

                    rests_on_period.append(rest_var)

        # rest between start of period and first staffed shift
        for s1 in shifts_on_period:
            rest = s1['start'] - period_start

            if rest > 0:
                in_between_shifts = list(filter(lambda x: x['start'] < s1['start'], shifts_on_period))

                not_staffed_on_in_between_shifts = model.NewBoolVar(uuid_func())
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) == 0).OnlyEnforceIf(not_staffed_on_in_between_shifts)
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) > 0).OnlyEnforceIf(not_staffed_on_in_between_shifts.Not())

                staffed_shift_with_length = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(staffed_shift_with_length == rest * _allocations[(s1['id'], person)])

                rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.AddMultiplicationEquality(rest_var, [staffed_shift_with_length, not_staffed_on_in_between_shifts])

                rests_on_period.append(rest_var)

        # rest between end of period and last staffed shift
        for s1 in shifts_on_period:
            rest = period_end - s1['end']

            if rest > 0:
                in_between_shifts = list(filter(lambda x: x['end'] > s1['end'], shifts_on_period))
                not_staffed_on_in_between_shifts = model.NewBoolVar(uuid_func())
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) == 0).OnlyEnforceIf(not_staffed_on_in_between_shifts)
                model.Add(sum(_allocations[(s['id'], person)] for s in in_between_shifts) > 0).OnlyEnforceIf(not_staffed_on_in_between_shifts.Not())

                staffed_shift_with_length = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.Add(staffed_shift_with_length == rest * _allocations[(s1['id'], person)])

                rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
                model.AddMultiplicationEquality(rest_var, [staffed_shift_with_length, not_staffed_on_in_between_shifts])

                rests_on_period.append(rest_var)

        # rest between start and end of period, if staffed on no shift
        not_staffed_on_any_shifts = model.NewBoolVar(uuid_func())
        model.Add(sum(_allocations[(s['id'], person)] for s in shifts_on_period) == 0).OnlyEnforceIf(
            not_staffed_on_any_shifts)
        model.Add(sum(_allocations[(s['id'], person)] for s in shifts_on_period) > 0).OnlyEnforceIf(
            not_staffed_on_any_shifts.Not())

        rest_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.Add(rest_var == not_staffed_on_any_shifts * period)

        rests_on_period.append(rest_var)

        # no rest at all
        rests_on_period.append(model.NewConstant(0))

        max_rest_on_period_var = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        model.AddMaxEquality(max_rest_on_period_var, rests_on_period)

        # slack_pos = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
        # slack_neg = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())

        # model.Add(max_rest_on_period_var - slack_pos + slack_neg == 4)

        # slacks.append(slack_pos)
        # slacks.append(slack_neg)

        slacks.append(max_rest_on_period_var)

    # sum_slacks = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    # model.Add(sum_slacks == sum(slacks))

    # max_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    # model.AddMaxEquality(max_slack, slacks)

    min_slack = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid_func())
    model.AddMinEquality(min_slack, slacks)

    variable = min_slack

    return {
        'variable': variable,
        'targeted_value': 0
    }
