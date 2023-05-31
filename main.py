import json
from rich.console import Console
from rich.table import Table
from rich.segment import Segment
from ortools.sat.python import cp_model
import rules


class Person:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Shift:
    def __init__(self, id, start, end, length, allocation, locked=False):
        self.id = id
        self.start = start
        self.end = end
        self.length = length
        self.allocation = allocation
        self.locked = locked


class Rule:
    def __init__(self, id, type, params):
        self.id = id
        self.type = type
        self.params = params


def score(stages_costs):
    score = 0
    quotient = 0

    for i in range(len(stages_costs)):
        score += (1 / 10 * min(10, stages_costs[i])) * (len(stages_costs) - i)
        quotient += len(stages_costs) - i

    if quotient == 0:
        quotient = 1
    score = 1 - score / quotient
    return score


last_uuid = 0


def uuid():
    global last_uuid
    last_uuid += 1
    return str(last_uuid)


INT_VAR_MIN = 0
INT_VAR_MAX = 1000000
INT_VAR_MAX_FINAL_PROD = 1000000000

console = Console()
if not console.color_system:
    console = Console(color_system="256")


def allocations_from_hint(allocations_hints, persons, shifts):
    allocations = []
    for s in shifts:
        shift = {'id': s['id'], 'allocation': []}
        for p in persons:
            if (s['id'], p['id']) in allocations_hints:
                if allocations_hints[(s['id'], p['id'])]:
                    shift['allocation'].append(p['id'])
        allocations.append(shift)
    return allocations


def rules_status_formatting(rules_status, rules_stages):
    formatted_rules_status = []
    originalIds = []
    for stage in rules_stages:
        for rule in stage:
            if rule['originalId'] not in originalIds:
                formatted_rules_status.append({'id': rule['originalId'], 'status': rules_status[rule['originalId']]})
                originalIds.append(rule['originalId'])

    return formatted_rules_status


def solve(shifts, persons, rules_stages, update_callback):
    # for callback purpose only
    rules_status = {}
    for stage in rules_stages:
        for rule in stage:
            rules_status[rule["originalId"]] = "PENDING"
    status = 'RUNNING'
    if len(rules_stages) > 0:
        for rule in rules_stages[0]:
            rules_status[rule["originalId"]] = "RUNNING"
    else:
        status = 'SUCCESS'
    update_callback(status=status,
                    result=[],
                    rules=rules_status_formatting(rules_status, rules_stages))

    solved_stages = []
    allocations_hints = {}

    for i in range(len(rules_stages)):
        stage = rules_stages[i]

        result = solve_stage(shifts, persons, stage, solved_stages, allocations_hints)

        if result is None:
            break

        solved_stage = {
            'cost': 0,
            'rules': []
        }

        for rule in stage:
            solved_stage['cost'] += result['rules'][rule['id']]['slack_pos'] + result['rules'][rule['id']]['slack_neg']
            solved_stage['rules'].append({
                'id': rule['id'],
                'type': rule['type'],
                'operator': rule['operator'] if 'operator' in rule else 'EQUAL',
                'params': rule['params'],
                'slack_pos': result['rules'][rule['id']]['slack_pos'],
                'slack_neg': result['rules'][rule['id']]['slack_neg']
            })

        solved_stages.append(solved_stage)

        allocations_hints = result['allocations']

        # for callback purpose only
        for rule in stage:
            rules_status[rule["originalId"]] = "SUCCESS"
        status = 'RUNNING'
        if len(rules_stages) > i + 1:
            for rule in rules_stages[i + 1]:
                rules_status[rule["originalId"]] = "RUNNING"
        else:
            status = 'SUCCESS'
        update_callback(status=status,
                        result=allocations_from_hint(allocations_hints=allocations_hints,
                                                     persons=persons,
                                                     shifts=shifts),
                        rules=rules_status_formatting(rules_status, rules_stages))

    console.print(f'Score = {round(score(list(map(lambda x: x["cost"], solved_stages))) * 100)} %', style='bold magenta')

    # return allocations_from_hint(allocations_hints=allocations_hints, persons=persons, shifts=shifts)


def solve_stage(shifts, persons, rules_to_solve, solved_stages, allocations_hints):
    model = cp_model.CpModel()

    _allocations = {}
    for s in shifts:
        for p in persons:
            if not s['locked']:
                _allocations[(s['id'], p['id'])] = model.NewBoolVar(uuid())
                if allocations_hints:
                    model.AddHint(_allocations[(s['id'], p['id'])], allocations_hints[(s['id'], p['id'])])
            else:
                _allocations[(s['id'], p['id'])] = model.NewConstant(s['allocation'] == p['id'])

        # one person max per shift
        # model.Add(sum([_allocations[(s['id'], p['id'])] for p in persons]) <= 1)

        # one person per shift
        model.Add(sum([_allocations[(s['id'], p['id'])] for p in persons]) == 1)

    # overlaps not allowed for a single person
    for i in range(len(shifts)):
        for j in range(i+1, len(shifts)):
            overlap = max(0, min(shifts[i]['end'], shifts[j]['end']) - max(shifts[i]['start'], shifts[j]['start']))
            if overlap > 0:
                for p in persons:
                    model.Add(_allocations[(shifts[i]['id'], p['id'])] + _allocations[(shifts[j]['id'], p['id'])] <= 1)

    _shifts = {}
    for s in shifts:
        _shifts[s['id']] = {
            'start': model.NewConstant(s['start']),
            'end': model.NewConstant(s['end']),
            'length': model.NewConstant(s['length']),
        }

    _rules = {}
    for stage in solved_stages:
        stage_cost = model.NewConstant(stage['cost'])
        for r in stage['rules']:
            _rules[r['id']] = {
                'type': r['type'],
                'operator': r['operator'] if ('operator' in r) else 'EQUAL',
                'params': r['params'],
                'slack_pos': model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid()),
                'slack_neg': model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
            }
            add_rule_to_model(_rules[r['id']], model, shifts, _shifts, persons, _allocations)
        model.Add(
            stage_cost == sum(_rules[r['id']]['slack_pos'] + _rules[r['id']]['slack_neg'] for r in stage['rules']))

    for r in rules_to_solve:
        _rules[r['id']] = {
            'type': r['type'],
            'operator': r['operator'] if ('operator' in r) else 'EQUAL',
            'params': r['params'],
            'slack_pos': model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid()),
            'slack_neg': model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
        }
        add_rule_to_model(_rules[r['id']], model, shifts, _shifts, persons, _allocations)

    if len(rules_to_solve) > 0:
        slacks_sum = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
        model.Add(slacks_sum == sum([_rules[r['id']]['slack_pos'] for r in rules_to_solve]
                                    + [_rules[r['id']]['slack_neg'] for r in rules_to_solve]))

        slack_max = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX, uuid())
        model.AddMaxEquality(slack_max, [_rules[r['id']]['slack_pos'] for r in rules_to_solve]
                             + [_rules[r['id']]['slack_neg'] for r in rules_to_solve])

        objective_func = model.NewIntVar(INT_VAR_MIN, INT_VAR_MAX_FINAL_PROD, uuid())
        model.AddProdEquality(objective_func, [slacks_sum, slack_max])

        model.Minimize(objective_func)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        console.print(f'Total cost = {solver.ObjectiveValue()}', style='bold magenta')

        for r in rules_to_solve:
            cost = solver.Value(_rules[r['id']]['slack_pos']) - solver.Value(_rules[r['id']]['slack_neg'])
            if cost == 0:
                console.print(f'☀️ {_rules[r["id"]]["type"]}', style='bold magenta')
            else:
                console.print(f'⛅ {_rules[r["id"]]["type"]} : {"+" if cost > 0 else ""}{cost}', style='bold magenta')

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Person", style="dim", width=12)
        for s in shifts:
            table.add_column(f"{s['id']}", style="dim", width=12)
        for p in persons:
            table.add_row(
                p['name'], *[f"{'x' if solver.Value(_allocations[(s['id'], p['id'])]) else ''}" for s in shifts]
            )
        console.print(table)

    else:
        print('No solution found.')
        print(['UNKNOWN', 'MODEL_INVALID', 'FEASIBLE', 'INFEASIBLE', 'OPTIMAL'][status])
        return

    result = {
        'rules': {},
        'allocations': {},
    }

    for r in rules_to_solve:
        result['rules'][r['id']] = {
            'slack_pos': solver.Value(_rules[r['id']]['slack_pos']),
            'slack_neg': solver.Value(_rules[r['id']]['slack_neg'])
        }

    for s in shifts:
        for p in persons:
            result['allocations'][(s['id'], p['id'])] = solver.Value(_allocations[(s['id'], p['id'])])

    return result


def add_rule_to_model(_rule, model, shifts, _shifts, persons, _allocations):
    slack_pos = _rule['slack_pos']
    slack_neg = _rule['slack_neg']

    rule_model = {
        'variable': None,
        'targeted_value': -1
    }

    if _rule['type'] == 'NUMBER_OF_SHIFTS':
        rule_model = rules.number_of_shifts2.get(_rule, shifts, _allocations)

    elif _rule['type'] == 'NUMBER_OF_HOURS':
        rule_model = rules.number_of_hours_on_interval.get(_rule, shifts, _allocations)

    elif _rule['type'] == 'WISHES':
        rule_model = rules.wishes.get(_rule, shifts, _allocations)

    elif _rule['type'] == 'MINIMUM_REST_HOURS_BETWEEN_SHIFTS':
        #rule_model = rules.minimum_rest_hours.get(_rule, model, shifts, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)
        rule_model = rules.rest_hours_between_shifts.get(_rule, shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'REST_HOURS_BY_PERIOD':
        #rule_model = rules.minimum_rest_hours.get(_rule, model, shifts, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)
        rule_model = rules.rest_hours_between_shifts.get(_rule, shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'REST_HOURS_AFTER_SHIFTS':
        rule_model = rules.rest_hours_after_shifts.get(_rule, model, shifts, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'NUMBER_OF_HOURS_BY_PERIOD':
        rule_model = rules.hours_by_period.get(_rule, model, shifts, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'NUMBER_OF_HOURS_IN_COMMON':
        rule_model = rules.number_of_hours_in_common.get(_rule, model, shifts, _allocations, uuid)

    elif _rule['type'] == 'ALL_HOURS_IN_COMMON':
        rule_model = rules.all_hours_in_common.get(_rule, model, shifts, _allocations, uuid)

    elif _rule['type'] == 'NUMBER_OF_SHIFTS_IN_COMMON':
        rule_model = rules.number_of_shifts_in_common.get(_rule, model, shifts, _allocations, uuid)

    elif _rule['type'] == 'GATHER_REST_HOURS':
        rule_model = rules.gather_rest_hours.get(_rule, model, shifts, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'NUMBER_OF_PERSONS':
        rule_model = rules.number_of_persons.get(_rule, persons, _allocations)

    elif _rule['type'] == 'DIVIDE_SHIFTS':
        rule_model = rules.divide_shifts.get(_rule, shifts, model, _allocations, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'NO_OVERLAPS':
        rule_model = rules.no_shifts_overlaps.get(_rule, model, shifts, _allocations, uuid)

    elif _rule['type'] == 'NUMBER_OF_HOURS_ON_INTERVAL':
        rule_model = rules.number_of_hours_on_interval.get(_rule, shifts, _allocations)

    elif _rule['type'] == 'FLOATING_BLANK_PERIOD':
        rule_model = rules.floating_blank_period.get(_rule, shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'FLOATING_BLANK_PERIODS':
        rule_model = rules.floating_blank_periods.get(_rule, shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX)

    elif _rule['type'] == 'REST_HOURS':
        rule_model = rules.rest_hours.get(_rule, shifts, _allocations, model, uuid, INT_VAR_MIN, INT_VAR_MAX)

    # elif _rule['type'] == 'ONE_PERSON_BY_SHIFT':
    #    rule_model = rules.one_person_by_shift.get(model, shifts, persons, _allocations)

    if _rule['operator'] == 'EQUAL':
        model.Add(rule_model['variable'] - slack_pos + slack_neg == rule_model['targeted_value'])

    elif _rule['operator'] == 'MAXIMUM':
        model.Add(rule_model['variable'] - slack_pos + slack_neg < rule_model['targeted_value'])
        model.Add(slack_neg == 0)

    elif _rule['operator'] == 'MINIMUM':
        model.Add(rule_model['variable'] - slack_pos + slack_neg > rule_model['targeted_value'])
        model.Add(slack_pos == 0)

    elif _rule['operator'] == 'MAXIMUM_OR_EQUAL':
        model.Add(rule_model['variable'] - slack_pos + slack_neg <= rule_model['targeted_value'])
        model.Add(slack_neg == 0)

    elif _rule['operator'] == 'MINIMUM_OR_EQUAL':
        model.Add(rule_model['variable'] - slack_pos + slack_neg >= rule_model['targeted_value'])
        model.Add(slack_pos == 0)
    else:
        model.Add(rule_model['variable'] - slack_pos + slack_neg == rule_model['targeted_value'])


if __name__ == '__main__':
    f = open('data.json')
    data = json.load(f)

    shifts = data['shifts']
    persons = data['persons']
    rules_stages = data['rules']

    f.close()

    def update_callback(status, result, rules):
        print('update')

    solve(shifts, persons, rules_stages, update_callback)
