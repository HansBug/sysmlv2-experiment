package Types { state def Controller { entry; then Idle; state Idle; state Active { entry; then Run; state Run; } transition turnOn first Idle if true then Active; } }
