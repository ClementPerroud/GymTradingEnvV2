from decimal import Decimal, getcontext

getcontext().prec = 8
SETTINGS = {
    "tolerance" : Decimal(f"1E-{getcontext().prec - 2}")
}
