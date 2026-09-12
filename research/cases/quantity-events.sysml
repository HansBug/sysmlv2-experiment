package QuantityEvents {
    private import ScalarValues::*;
    private import SI::*;

    item def Tick;

    state def Controller {
        attribute altitude subsets ISQ::length default 0 [m];
        first start then ground;
        state ground;
        state air;
        accept Tick if altitude >= 10 [m] then air;
        accept Tick if altitude < 10 [m] then ground;
    }
}
