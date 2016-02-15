# Simulate Load-Based-Power-Saving mechanism

## Intro

LBPS was invented for WiMax, the core concept is to accumulate data until it reach the threshold rather than transmit right after receive data. By LBPS, receiver could extend the sleep cycle and improve its power efficiency. As time goes by, our lab get involved in LTE research and decided to modify the LBPS for adapting LTE architecture.

* First generation - LTE-LBPS: one-hop in FDD,  LBPS-Aggr/LBPS-Split/LBPS-Merge
* Second generation - LTE-LBPS-RN: two-hop in FDD, UE-1st/RN-1st
* Third generation - LTE-LBPS: one-hop in TDD, virtual-timeline/mapping

And my research is for fourth generation of LBPS which is two-hop in TDD.

So far, the basic idea include TopDown/BottomUp and MinCycle/MergeCycle.

## System model

**Device**

* DeNB
* RN: Type-1 RN
* UE

**Process**

* Poisson process: MM1
