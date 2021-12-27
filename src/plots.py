import matplotlib.pyplot as plt


# plot use case 1
def plot_uc1(fuel_stations, boundaries, traffic, circles):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    # circles.plot(ax=ax)
    traffic.plot(ax=ax)
    fuel_stations.plot(ax=ax, marker='o', color='red', markersize=5)
    boundaries.boundary.plot(ax=ax, color='black', edgecolor='black')


# plot use case 2
def plot_uc2(pir, boundaries):
    fig, ax = plt.subplots()

    ax.set_aspect('equal')

    pir.plot(ax=ax, marker='o', markersize=5, legend='false')
    boundaries.boundary.plot(ax=ax, color='black', edgecolor='black')


# plot use case 3
def plot_uc3(wir, boundaries):
    fig, ax = plt.subplots()

    ax.set_aspect('equal')

    wir.plot(column='population', ax=ax, marker='o', markersize=5, legend='true',
             legend_kwds={'label': "Energysum per 100m square"}, cmap='Reds')  # scheme='quantiles'
    boundaries.boundary.plot(ax=ax, color='black', edgecolor='black')


# plot use case 4
def plot_uc4(wir, boundaries):
    fig, ax = plt.subplots()

    ax.set_aspect('equal')

    wir.plot(column='energysum', ax=ax, marker='o', markersize=5, legend='true',
             legend_kwds={'label': "Energysum in area in kWh"})
    boundaries.boundary.plot(ax=ax, color='black', edgecolor='black')


def plot_energy_sum(energysum):
    energysum.plot.line(y=[1], use_index=True)

    plt.show()
