package Inheritance { private import Types::*; state def Derived :> Controller; part def Device { exhibit state controller : Derived; } }
