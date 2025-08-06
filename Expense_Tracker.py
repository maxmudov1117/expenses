import json
from datetime import datetime

filename = "expense.json"
time = datetime.now


def load_expense():
    with open(filename, 'r') as file:
        expenses = json.load(file)
        return expenses


def get_next_id(expenses):
    if not expenses:
        return 1
    max_id = 0
    for task in expenses:
        if task['id'] > max_id:
            max_id = task['id']
    return max_id + 1


def add(description, amount: int):
    try:
        expenses = load_expense()
    except Exception():
        expenses = []

    new_expense = {
        'id': get_next_id(expenses),
        'created_at': str(datetime.now())[0:10],
        'description': description,
        'amount': f"${amount}"
    }
    expenses.append(new_expense)

    with open(filename, 'w') as file:
        json.dump(expenses, file, indent=4, ensure_ascii=False)


def list_expenses():
    expenses = load_expense()

    if not expenses:
        print("Hech qanday xarajat topilmadi.")

    print(f"{'ID':<4} {'Date':<12} {'Description':<15} {'Amount':>7}")

    for expense in expenses:
        print(f"{expense['id']:<4} {expense['created_at']:<12} {expense['description']:<15} {expense['amount']:>6}")
    return ''


def summary():
    expenses = load_expense()
    s = 0
    for expense in expenses:
        if expense['amount']:
            amount = expense['amount'][1:]
            amount = int(amount)
            s += amount
        else:
            return []
    return s
def summary_1(month):
    expenses = load_expense()
    s = 0
    for expense in expenses:
        par = expense['created_at'].split("-")
        date = int(par[1])
        if month == date:
            amoun = expense['amount'][1:]
            amoun = int(amoun)
            s += amoun
    return s

def delete(id):
    expenses = load_expense()
    for expense in expenses:
        if expense['id'] == id:
            expenses.remove(expense)
            break
        else:
            print("Bunday id dagi ma'lumot mavjud emas")
    with open(filename, 'w') as file:
        json.dump(expenses, file, ensure_ascii=False, indent=4)


def get_id():
    return len(load_expense())

def oy_nomi_ber(month: int) -> str:
    oylar = {
        1: "Yanvar",
        2: "Fevral",
        3: "Mart",
        4: "Aprel",
        5: "May",
        6: "Iyun",
        7: "Iyul",
        8: "Avgust",
        9: "Sentabr",
        10: "Oktabr",
        11: "Noyabr",
        12: "Dekabr"
    }
    return oylar.get(month, "Nomaʼlum oy")

while True:
    text = input("$ expense-tracker ")
    if text.startswith("exit"):
        break
    elif text.startswith("add"):
        part = text.split()
        description = part[2]
        amount = int(part[4])
        add(description, amount)
        print(f"Expense added successfully (ID: {get_id()})")
    elif text.startswith('list'):
        print(list_expenses())
    elif text.startswith('summary'):
        print(f"Total expenses: {summary()}")
    elif text.startswith("delete"):
        part = text.split()
        id = int(part[2])
        delete(id)
        print(f"Expense added successfully (ID: {id})")
    elif text.startswith("month"):
        parts = text.split()
        month = int(parts[2])
        oy_nomi = oy_nomi_ber(month)
        summary_1(month)
        print(f"Total expenses for {oy_nomi}: ${summary_1(month)}")



