from scipy.stats import poisson


def prob_acc_under(lambd, threshold, sleep_cycle):
    assert isinstance(threshold, int), 'please confirm the type of threshold'
    prob_acc = 0

    while threshold >= 0:
        prob_acc += poisson.pmf(threshold, lambd*sleep_cycle)
        threshold -= 1

    return prob_acc

def prob_acc_over(lambd, threshold, sleep_cycle):
    prob = prob_acc_under(lambd, threshold, sleep_cycle)
    return 1-prob if prob else 1

def get_sleep_cycle(lambd, data_threshold, prob_threshold=0.8):
    sleep_cycle = 1

    while True:
        prob_acc = prob_acc_over(lambd, data_threshold, sleep_cycle)
        if prob_acc > prob_threshold:
            break
        sleep_cycle += 1

    return sleep_cycle

def get_data_accumulation(lambd, sleep_cycle, prob_threshold=0.8):
    packet = 0

    while True:
        prob_acc = prob_acc_under(lambd, packet, sleep_cycle)
        assert prob_acc
        if prob_acc > prob_threshold:
            break
        packet += 1

    return packet
