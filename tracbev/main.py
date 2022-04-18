import matplotlib.pyplot as plt
import argparse

from tracbev import TracBEV


def main():
    print('Starting Program for Distribution of Energy...')

    argparser = argparse.ArgumentParser(description='TracBEV tool for allocation of charging infrastructure')
    argparser.add_argument('scenario', default="default_scenario", nargs='?',
                           help='Set name of the scenario directory')
    p_args = argparser.parse_args()

    tracbev = TracBEV(p_args.scenario)
    tracbev.run()
    plt.show()


if __name__ == '__main__':
    main()
