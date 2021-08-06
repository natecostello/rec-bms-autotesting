from pandas import read_csv
import matplotlib.pyplot as plt
import os
import sys

os.system('rm *.png')



# filename = 'rising_voltage_test.csv'
filename = str(sys.argv[1])

df = read_csv(filename, header=0, parse_dates=[0], index_col=0)

# iterating the columns
for col in df.columns:
    print(col)


parsedTitle = filename.split('.')[0]

# # max cell voltage vs charge current limit
# # example of dual y axis
# fig, ax = plt.subplots()
# ax.plot(df[['rec-q-can.Max Cell Voltage.V']], color="red")
# ax.set_ylabel("Max Cell Voltage [V]", color="red")
# ax2 = ax.twinx()
# ax2.plot(df[['rec-q-can.CCL.A']], color="blue")
# ax2.set_ylabel("CCL [A]", color="blue")

# plt.show()

# plot_description = 'Cell Voltage and CCL'
# plot_title = plot_description + ' ' + parsedTitle
# plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
# plt.title(plot_title)

# plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
# plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# max temp vs several params for falling temp
fig, axs = plt.subplots(3, sharex=True)
plot_description = 'Min Temperature'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# min cell voltage vs time
axs[0].plot(df[['rec-q-can.Min Temperature.C']], label="Min Temperature", color="red")
# charge voltage limit vs time
axs[1].plot(df[['rec-q-can.CCL.A']], label="Charge Current Limit", color="blue")
# SOC vs time
axs[2].plot(df[['rec-q-binary.charge_enable.binary']], label="Charge Enable", color="green")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# max temp vs several params for rising temp
fig, axs = plt.subplots(4, sharex=True)
plot_description = 'Max Temperature'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# min cell voltage vs time
axs[0].plot(df[['rec-q-can.Max Temperature.C']], label="Max Temperature", color="red")
# charge voltage limit vs time
axs[1].plot(df[['rec-q-can.CCL.A']], label="Charge Current Limit", color="blue")
# SOC vs time
axs[2].plot(df[['rec-q-binary.charge_enable.binary']], label="Charge Enable", color="green")
# Charge Enable vs time
axs[3].plot(df[['rec-q-binary.contactor.binary']], label="Contactor", color="orange")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# min cell voltage vs several params for disch
fig, axs = plt.subplots(4, sharex=True)
plot_description = 'Min Cell Voltage and End of Discharge'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# min cell voltage vs time
axs[0].plot(df[['rec-q-can.Min Cell Voltage.V']], label="Min Cell Voltage", color="red")
# charge voltage limit vs time
axs[1].plot(df[['rec-q-can.DCL.A']], label="Discharge Current Limit", color="blue")
# SOC vs time
axs[2].plot(df[['rec-q-can.SOC_HR.%']], label="SOC", color="green")
# Charge Enable vs time
axs[3].plot(df[['rec-q-binary.contactor.binary']], label="Contactor", color="orange")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots
# max cell voltage vs charge current limit
fig, axs = plt.subplots(2, sharex=True)
plot_description = 'Max Cell Voltage and CCL'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# max cell voltage vs time
axs[0].plot(df[['rec-q-can.Max Cell Voltage.V']], label="Max Cell Voltage", color="red")
# charge current limit vs time
axs[1].plot(df[['rec-q-can.CCL.A']], label="Charge Current Limit", color="blue")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# min cell voltage vs several params
fig, axs = plt.subplots(4, sharex=True)
plot_description = 'Min Cell Voltage and End of Charge'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# min cell voltage vs time
axs[0].plot(df[['rec-q-can.Min Cell Voltage.V']], label="Min Cell Voltage", color="red")
# charge voltage limit vs time
axs[1].plot(df[['rec-q-can.CVL.V']], label="Charge Voltage Limit", color="blue")
# SOC vs time
axs[2].plot(df[['rec-q-can.SOC_HR.%']], label="SOC", color="green")
# Charge Enable vs time
axs[3].plot(df[['rec-q-binary.charge_enable.binary']], label="Charge Enable", color="orange")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# min cell voltage vs several params
fig, axs = plt.subplots(4, sharex=True)
plot_description = 'Max Cell Voltage and End of Charge'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)
# min cell voltage vs time
axs[0].plot(df[['rec-q-can.Max Cell Voltage.V']], label="Max Cell Voltage", color="red")
# charge voltage limit vs time
axs[1].plot(df[['rec-q-can.CVL.V']], label="Charge Voltage Limit", color="blue")
# Charge Enable vs time
axs[2].plot(df[['rec-q-binary.charge_enable.binary']], label="Charge Enable", color="orange")
# Contactor vs time
axs[3].plot(df[['rec-q-binary.contactor.binary']], label="Contactor Status", color="green")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")

# stack subplots 
# max cell voltage vs relay cutoff 
fig, axs = plt.subplots(2, sharex=True)

plot_description = 'Max Cell Voltage and Contactor'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
fig.suptitle(plot_title)

# max cell voltage vs time
axs[0].plot(df[['rec-q-can.Max Cell Voltage.V']], label="Max Cell Voltage", color="red")

# contactor
axs[1].plot(df[['rec-q-binary.contactor.binary']], label="Contactor Status", color="blue")

for ax in axs:
    ax.label_outer()
    ax.legend(loc="upper left", bbox_to_anchor=[0, 1], fancybox=True)

plt.show()
plt.savefig(plot_filename, bbox_inches="tight")




# cell voltages
df[['rec-q-can.Min Cell Voltage.V','rec-q-can.Max Cell Voltage.V']].plot()

plot_description = 'Cell Voltages'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.ylim(2.5,3.9)
plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.savefig(plot_filename, bbox_inches="tight")

# Battery temp and max min temp
df[['rec-q-can.Battery Temp.C', 'rec-q-can.Min Temperature.C', 'rec-q-can.Max Temperature.C']].plot()
plot_description = 'Battery Temperature'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

#plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.legend(loc="center right", bbox_to_anchor=[1, 0.5], fancybox=True)
plt.savefig(plot_filename, bbox_inches="tight")

# Binary values
df[['rec-q-binary.internal_relay.binary', 'rec-q-binary.charge_enable.binary', 'rec-q-binary.system_plus.binary', 'rec-q-binary.contactor.binary']].plot()

plot_description = 'Binary Values'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.savefig(plot_filename, bbox_inches="tight")

# SOC and SOH
df[['rec-q-can.SOC_HR.%', 'rec-q-can.SOH.%']].plot()

plot_description = 'SOC SOH'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.ylim(0,110)
plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.savefig(plot_filename, bbox_inches="tight")

# Capacity
df[['rec-q-can.Rated Capacity.AH', 'rec-q-can.Remaining Capacity.AH']].plot()

plot_description = 'Battery Capacity'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.ylim(0,600)
plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.savefig(plot_filename, bbox_inches="tight")

# VL and Battery Voltage
df[['rec-q-can.CVL.V', 'rec-q-can.DVL.V', 'rec-q-can.Battery Voltage.V']].plot()

plot_description = 'Battery Voltage'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-').lower() + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.legend(loc="center left", bbox_to_anchor=[0, 0.5], fancybox=True)
plt.savefig(plot_filename, bbox_inches="tight")

# CL and Battery Current
# df[['rec-q-can.CCL.A', 'rec-q-can.DCL.A', 'rec-q-can.Battery Current.A']].plot()
modified_df = df[['rec-q-can.CCL.A', 'rec-q-can.DCL.A', 'rec-q-can.Battery Current.A']]

def negate(value):
    """negates"""
    return value * -1

# warns but works
modified_df['rec-q-can.DCL.A'] = modified_df['rec-q-can.DCL.A'].apply(negate)
modified_df[['rec-q-can.CCL.A', 'rec-q-can.DCL.A', 'rec-q-can.Battery Current.A']].plot()

plot_description = 'Battery Current'
plot_title = plot_description + ' ' + parsedTitle
plot_filename = plot_description.replace(' ', '-') + '-' + parsedTitle + '.png'
plt.title(plot_title)

plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left")
plt.savefig(plot_filename, bbox_inches="tight")

"""
Logical groupings of data worth having prebaked:
Cell Voltages
Battery temp and max min temp
Binary values
SOC and SOH
Rated Capacity vs Remaining Capacity
DVL and CVL vs Battery Voltage
DCL and CCL vs Battery Amps ** Probably worth flipping sign on DCL (for plot at least)


"""

