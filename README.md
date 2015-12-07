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
# Unitest for MM1 and MM2
python queuing.py
```
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

## Note

Using matplotlib.pyplot for ploting the chart

```
sudo apt-get install python-pipe
sudo apt-get install libfreetype6-dev libxft-dev
sudo pip install numpy scipy matplotlib
```
