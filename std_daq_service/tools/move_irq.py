import argparse

from std_daq_service.tools.tune_network import set_irq_to_core


def main():
    parser = argparse.ArgumentParser(description='Move IRQ to core')
    parser.add_argument("irq", type=int, help="Interrupt number; first column in /proc/interrupts")
    parser.add_argument('core_id', type=int, help='Zero based index of core to move the interrupt to.')
    args = parser.parse_args()

    network_interface = args.network_interface
    irq = args.irq
    core_id = args.irq

    set_irq_to_core(irq, core_id)


if __name__ == "__main__":
    main()
