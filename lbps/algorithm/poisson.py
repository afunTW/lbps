from scipy.stats import poisson


def get_sleep_cycle(lambd, data_threshold, prob_threshold=0.8):
    sleep_cycle = 1

    while True:
        mu = lambd * sleep_cycle
        prob = [poisson.pmf(i, mu) for i in range(int(data_threshold))]
        skip = False

        for i, p in enumerate(prob):
            if 1 - sum(prob[:i]) < prob_threshold:
                skip = True
                break

        if skip:
            sleep_cycle += 1
        else:
            break

    return sleep_cycle

# FIXME: need test
def get_data_accumulation(lambd, sleep_cycle, prob_threshold=0.8):
    packet = 0

    while True:
        mu = lambd * sleep_cycle
        prob = [poisson.pmf(i, mu) for i in range(packet)]
        skip = False

        for i, p in enumerate(prob):
            if sum(prob[:i]) > prob_threshold:
                skip = True
                break

        if skip:
            packet += 1
        else:
            break

    return packet
