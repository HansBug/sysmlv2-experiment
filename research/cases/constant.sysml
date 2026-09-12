package NewSyntax { private import ScalarValues::*; state def S { constant attribute limit : Integer = 1; state A; state B; transition t first A if limit > 0 then B; } }
