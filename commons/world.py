from . import config


def regrow(stock):
    return min(config.K, stock + config.R * stock * (1 - stock / config.K))


def scale_catches(catches, stock):
    total = sum(catches)
    if total <= stock or total <= 0:
        return list(catches), total
    factor = stock / total
    scaled = [int(c * factor) for c in catches]
    return scaled, sum(scaled)


def apply_round(stock_before, catches, wealths):
    catches, total_catch = scale_catches(catches, stock_before)
    stock = stock_before - total_catch
    stock_after = regrow(stock)
    wealths = [w + c - config.LIVING for w, c in zip(wealths, catches)]
    dead = stock_after < config.F_DEAD
    return stock_after, catches, total_catch, wealths, dead
