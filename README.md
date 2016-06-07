# Integrated Sleep Scheduling for Multiple Relays and UEs in LTE-TDD

## Intro

We designed the Load-Based-Power-Saving algorithm for WiMAX few years ago since the WiMAX still the prominent and potential 4G network architecture. As time went by, Long-Tern-Evolution dominate this field, and we redesign the LBPS algorithm for LTE architecture. At that time, the scenario of LBPS can only used in one hop, single cellular network with FDD.

So far, this research can approach more complicated scenario. Considering Relay node which is the key feature in LTE-Advanced, especially the Type-1 RN (inband, half duplex). The link from Donor-eNB(DeNB) to RN, we called backhaul link and the link from RN to user(UE), we called access link. RN can not do backhaul transmissino and access transmission at the same time, it have to decide the priority of transmission based on the current internet load and the buffer status.

We implement this power saving scheduling in TDD, therefore, we must to make the decision by TDD configuration. Besides, our scenario will integrated multiple relays and considering the different link qulaity.

## System model

**Packet arrival process**

Using Poisson model to simulate the behavior of packet arrival.

**Device**

One DeNB is essential and we deploy six fixed Type-1 RN in this cellular. Also, there have forty UE in each RN cell.
In conclusion, there have one DeNB, 6 RNs, and 240 UE in one single cell.

**CQI report**

Both of backhaul link and access link used wideband CQI reporting.

The range of CQI in each backhaul link is 10 to 15 and the range of CQI in each access link is 7 to 15. All of UEs will randomized the CQI and do reporting to RN, in the other hand, RNs will randomized the CQI and do reporting to DeNB.

## Problem

**LBPS in Time-Division-Duplex(TDD) mode**

* Virtual timeline
* Mapping

**LBPS in two hop TDD**

* TDD configuration
> * backhaul TDD configuration
> * access TDD configuration

## Algorithm

* Top-Down
> * aggr-aggr
> * split-aggr
> * merge-aggr

* Mincy-cle

* Merge-cycle

* Bottom-Up
> * mincycle-aggr
> * mincycle-split
> * mergecycle-merge