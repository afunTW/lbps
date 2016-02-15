# LTE_Simulation

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
![simresult](https://cloud.githubusercontent.com/assets/4820492/11652655/e074d3b0-9dd3-11e5-9a22-5b4e16de57a8.png)

## Note

Using matplotlib.pyplot for ploting the chart

```
sudo apt-get install python-pipe
sudo apt-get install libfreetype6-dev libxft-dev
sudo pip install numpy scipy matplotlib
```
