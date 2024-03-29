import argparse
import re

from std_daq_service.tools.monitor_irq import collect_irq_samples


def print_cpu_table(interface_regex, delta_time):
    meta, irqs, irqs2 = collect_irq_samples(interface_regex, delta_time)

    cpu_stats = {}
    print("{:<8} {:<8} {}".format('CORE_ID', 'N_INT', 'QUEUE_NAME(n_interrupts)'))
    for i_queue in range(len(meta)):
        queue_name = meta[i_queue]['queue_name']

        for core_id in range(len(irqs2[i_queue])):
            delta_irq = int(irqs2[i_queue][core_id]) - int((irqs[i_queue][core_id]))
            if core_id not in cpu_stats:
                cpu_stats[core_id] = []
            cpu_stats[core_id].append((delta_irq, queue_name))

    for core_id, queues_irqs  in cpu_stats.items():
        queues_irqs = sorted(queues_irqs, reverse=True)
        irq_string = ''
        n_interrupts = 0
        for delta_irq, queue_name in queues_irqs:
            if delta_irq > 0:
                irq_string += f'{queue_name}({delta_irq}) '
                n_interrupts += delta_irq

        print("{:<8} {:<8} {}".format(core_id, n_interrupts, irq_string))


def main():
    parser = argparse.ArgumentParser(description='Monitor ')
    parser.add_argument("--interface_regex", type=str, default='ens|eno|ib',
                        help="Regex match on QUEUE_NAME.")
    parser.add_argument('--delta_time', type=float, default=1,
                        help='Time to accumulate interrupts in seconds.')

    args = parser.parse_args()
    print_cpu_table(interface_regex=args.interface_regex, delta_time=args.delta_time)


if __name__ == "__main__":
    main()
