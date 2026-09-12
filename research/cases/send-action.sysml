package SendActionProbe {
    attribute def Signal;
    part receiver;

    state def Controller {
        entry; then idle;
        state idle {
            entry send new Signal() to receiver;
        }
    }
}
