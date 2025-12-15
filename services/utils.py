def get_quarter(date_obj):
    m = date_obj.month
    if m <= 3:
        return "Q1 (Jan-Mar)"
    elif m <= 6:
        return "Q2 (Apr-Jun)"
    elif m <= 9:
        return "Q3 (Sep-Sep)"
    return "Q4 (Oct-Dec)"
