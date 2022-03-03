import matplotlib.pyplot as plt
import pathlib


# plot hpc
def plot_uc(use_case, charge_points, uc_dict):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    # charge point plotting differs per use case
    if use_case == "hpc":
        charge_points.plot(ax=ax, marker='o', cmap='Set2', markersize=5,
                           column="exists", categorical=True)
    elif use_case == "public":
        charge_points.plot(ax=ax, marker='o', markersize=5, legend='false',
                           column="exists", cmap="Set1", categorical=True)
    elif use_case == "home":
        charge_points.plot(column='energy', ax=ax, marker='o', markersize=5, legend='true',
                           legend_kwds={'label': "Energysum per 100m square"}, cmap='cool')  # scheme='quantiles'
    elif use_case == "work":
        charge_points.plot(column='energy', ax=ax, marker='o', markersize=5, legend='true',
                           legend_kwds={'label': "Energysum in area in kWh"}, cmap='YlGnBu', vmin=0)

    uc_dict['region'].boundary.plot(ax=ax, color='black', edgecolor='black')
    plt.savefig(pathlib.Path(uc_dict["result_dir"], use_case + "_plot.svg"), bbox_inches='tight')


def plot_energy_sum(energysum):
    energysum.plot.line(y=[1], use_index=True)

    plt.show()
