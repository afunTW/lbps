# LTE_Simulation

## LTE_LBPS_RN in TDD

* LBPS-Aggr
* LBPS-Split
* LBPS-Merge
* LBPS with RN (RN 1st)
* LBPS with RN (UE 1st)
* LBPS in TDD (virtual timeline)
> * one-to-all mapping
> * continuous mapping
> * one-to-one first mapping

## queuing

* MM1, reference by [drvinceknight](https://github.com/drvinceknight/Simulating_Queues)
* MM2

```
# import as module
>> import queuing
>> tmp = queuing(1,1,1000000)
>> tmp.MM1()  # You can get the needed info after that
>> tmp.MM2()
>> tmp.mean_wait
>> tmp.mean_service_time
>> tmp.mean_time
>> tmp.utilization
```
```
# Unitest for MM1 and MM2
python queuing.py
```
It should show the figure like that
![figure_1](https://cloud.githubusercontent.com/assets/4820492/11636616/f7307ad6-9d57-11e5-9a3c-9c5cfc57333a.png)

## Note

Using matplotlib.pyplot for ploting the chart

```
sudo apt-get install python-pipe
sudo apt-get install libfreetype6-dev libxft-dev
sudo pip install numpy scipy matplotlib
```
