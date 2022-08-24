
macro ' [followingList] [
    [list [quote quote [followinglist]]]
]

//random ass comment

macro if [condition _then option1 _else option2] [
    [list ['cond condition option1 option2]]
]



macro func [somename arguments body] /* inline comments*/ [
    [let x [some calculation]] //wordt uitgevoert in de macro
    [list ['let somename [lambda arguments body]]]]
]



func somename [arg1 arg2] [
    [print arg1]
    [print arg2]
    [sum [list [1,2,3,4]]]
]


[somename "some" "string\n"]