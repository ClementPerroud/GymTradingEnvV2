from decimal import Decimal, getcontext

getcontext().prec = 15
SETTINGS = {
    "tolerance" : Decimal(f"1E-{getcontext().prec - 1}")
}
