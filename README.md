# LispLangInterpreter

An interpreter for a lisp-like language

## General goal

Achieving a lisp like language with F# inspired mutability, a more powerfull macro system where macros are (nearly) indistinguishable from regular functions, with built in support for effects and effect handlers (at least as far as I understand them).
This is meant as a fun project for myself.

## Features
- Fully functional (non mutable) by default, all mutability is achieved via effects
- ML inspired syntax
- Effect system with stop and continue
- Scoped lisp-like macros - All macros are scoped, meaning that making or importing a macro only effects code within the scope
- Open ended macros - Macros have access to all the AST beyond it, allowing for more flexible macro creation
- Macros can acces scoped values - Macros have acces to all value and functions in scope at the point of creation
- Easy to use code library system