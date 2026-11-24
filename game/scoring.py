def efficiency_percent(spent, optimal):
    if spent <= 0:
        return 0
    return round(optimal / spent * 100)


def stars_for_efficiency(efficiency):
    if efficiency >= 95:
        return 3
    if efficiency >= 80:
        return 2
    return 1
