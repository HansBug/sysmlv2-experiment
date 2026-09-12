package PerformSequenceProbe {
    action def StepA;
    action def StepB;

    state def Phase {
        do action workflow {
            first start;
            then action a : StepA;
            then action b : StepB;
            then done;
        }
    }

    state def InitialState;
    state def Controller {
        state initial : InitialState;
        state phase : Phase;
        transition first initial then phase;
    }
}
