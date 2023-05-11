import argparse
import logging
import socket
import subprocess
import yaml

_logger = logging.getLogger("tune_network")


def is_hostname_from_this_machine(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        local_hostname = socket.gethostbyaddr(ip_address)[0]
        _logger.info(f"Resolved local hostname {local_hostname}")
        return local_hostname == socket.gethostname()

    except Exception:
        _logger.exception("Cannot resolve local hostname.")
        return False


def get_module_id_to_cpu_id_map(machine_config):
    result = {}
    for service_config in machine_config['vars'][1]['microservices']:
        if service_config['prog_name'].startswith('std_udp_recv'):
            for instance in service_config['instances']:
                core_id = instance['cpus'][0]
                module_id = instance['params'][0]
                result[module_id] = core_id

    return result


def get_module_id_to_irq_map(interface):
    with open('/proc/interrupts') as input_file:
        lines = [x.split() for x in input_file.readlines() if interface in x]
    return {i: x[0][:-1] for i, x in enumerate(lines)}


def tune(machine_config, interface, start_udp_port):
    _logger.info(f'Tuning interface {interface} with start_udp_port {start_udp_port}.')

    map_module_to_cpu = get_module_id_to_cpu_id_map(machine_config=machine_config)
    map_module_id_to_irq = get_module_id_to_irq_map(interface)

    cmd = f"ethtool -u {interface} | grep Filter: | awk '{{print $2}}' | xargs -L1 ethtool -U {interface} delete"
    subprocess.run(cmd, shell=True)

    for module_id, cpu_id in map_module_to_cpu.items():
        irq = map_module_id_to_irq[module_id]
        irq_file = f"/proc/irq/{irq}/smp_affinity_list"

        with open(irq_file, 'w') as output_file:
            output_file.write(cpu_id)

        udp_port = int(start_udp_port) + module_id
        cmd = ["ethtool", "-U", interface, "flow-type", "udp4", "dst-port", str(udp_port), "action", str(module_id)]
        subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description='Tune network on receiver machine')
    parser.add_argument("deployment_config", type=str, help="Path to the site.yaml deployment config.")
    parser.add_argument('daq_config', type=str, help='Path to daq config file.')
    parser.add_argument('network_interface', type=str, help='Name of the network interface to tune.')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    network_interface = args.network_interface

    with open(args.deployment_config, 'r') as input_file:
        deployment_config = yaml.safe_load(input_file)

    with open(args.daq_config, 'r') as input_file:
        daq_config = yaml.safe_load(input_file)

    for machine_config in deployment_config:
        config_hostname = machine_config['hosts']
        _logger.info(f'Inspecting config hostname {config_hostname}.')

        if is_hostname_from_this_machine(machine_config['hosts']):
            tune(machine_config, network_interface, daq_config['start_udp_port'])
            break
    else:
        _logger.error("No hostname matches the current machine.")


if __name__ == "__main__":
    main()