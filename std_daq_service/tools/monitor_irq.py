import argparse
from time import sleep
import re


def collect_interface(queue_regex):
    with open('/proc/interrupts') as input_file:
        lines = [x.split() for x in input_file.readlines()[1:]]

    interface_lines = [x for x in lines if re.search(queue_regex, x[-1])]

    interface_meta = [{'line_n': i, 'irq': x[0][:-1], 'queue_name': x[-1]} for i, x in enumerate(interface_lines)]
    interface_interrupts = [x[1:33] for x in interface_lines]
    return interface_meta, interface_interrupts


def print_irq_table(interface_regex, delta_time):
    meta, irqs = collect_interface(interface_regex)
    sleep(delta_time)
    meta, irqs2 = collect_interface(interface_regex)

    result = []
    for irq_t1, irq_t2 in zip(irqs, irqs2):
        irq_result = {}

        for core_id, n_int in enumerate(zip(irq_t1, irq_t2)):
            diff = int(n_int[1]) - int(n_int[0])
            if diff > 0:
                irq_result[core_id] = diff

        result.append(irq_result)

    print("{:<8} {:<5} {:<20} {}".format('LINE_N', 'IRQ', 'QUEUE_NAME', 'N_DELTA_IRQS (core_id: n_interrupts)'))
    for irq_data, interrupts in zip(meta, result):
        if interrupts and re.search(r'\d', irq_data['irq']):
            print("{:<8} {:<5} {:<20} {}".format(irq_data['line_n'],
                                                 irq_data['irq'],
                                                 irq_data['queue_name'],
                                                 interrupts))


def main():
    parser = argparse.ArgumentParser(description='Monitor ')
    parser.add_argument("--interface_regex", type=str, default='ens|eno|ib',
                        help="Regex match on QUEUE_NAME.")
    parser.add_argument('--delta_time', type=float, default=1,
                        help='Time to accumulate interrupts in seconds.')

    args = parser.parse_args()
    print_irq_table(interface_regex=args.interface_regex, delta_time=args.delta_time)


if __name__ == "__main__":
    main()
