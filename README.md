# TupLang
A programming language for tuple processing with pipes. It was created for educational purposes only. The development has officially stopped and it is not recommended to use it for production purposes. The language is a part of the course [Principle of Programming Languages](https://www.cs.tut.fi/~popl/nykyinen/index.shtml) organised by Tampere University. The description of the language can be seen from the [project page](https://www.cs.tut.fi/~popl/nykyinen/project/index.shtml) of the course.

### Example of the syntax

The comments are denoted using the curly braces { }. 

    { Calculate the factorial of N. }
    
    N <- 10.
    [1..N] | * -> <factorialten>.
    ["I know that 10! is "] ++ <factorialten> | Print -> <dummyvar>.



    { A function that prints a value and it doubled, returns the doubled value. }
    define Print_and_double[aa]
    
    begin
      [aa, " doubled is", 2*aa] | Print -> <tuple>.
      = select:3[<tuple>]. { return the 3. element of tuple. }
    end.



    { Keyword each calls a function for every element in a tuple. }
    
    [1,5,2,8,4,5] | each:Print_and_double -> <doubles>.
    <doubles> | + -> <sumofdoubles>.
    sum <- select:1[<sumofdoubles>].
    != Print["Sum of doubles is ", sum].
    

## Description

ASTnodes used in the previous stage now have additional parameters. The nodes of expressions that can return a value either have a respective attribute “.value” or in case when they reference another variable using identifier, they have a parameter called “.eval” that contains a lambda expression that will return a value when called. The lambdas in “.eval” parameter expect a dictionary parameter with the values for variables needed. The variable identifiers are the keys and their values are dictionary values. All the nodes that need to be evaluated have a list of required parameters in “.params” attribute. 

#### Checks:
1) Variables, functions, and parameters have to be defined before being used, no double definitions allowed:
All the identifiers of the variables are added to the symbol table under “declared”-key. If value of variable is needed to be evaluated, the list of required parameters is checked. If the list contains a parameter that is not in symbol table, then it is referenced before the definition. The same checks goes for double definitions. If an identifier is already in the table, then it is being defined twice. Double definition in this implementation is forbidden to function definitions, constants and tuples. Variables can be redefined.

2) Parameters are only allowed to appear in the function in which they have been defined:
There are different scopes for declared variables. Whether a variables has been declared is checked within the scope of the variable and within the global scope also. 

3) The number of actual parameters in a function call has to match the number for formal parameters in the function definition:
There is additional dictionary for all the functions within the symbol table that has a function identifier as the key and the number of arguments as the value. The number is calculated from the “.args” attribute of the function – ASTNode. In addition to that all the function calls - nodes have the same attribute. Check is done by comparing the length of the call arguments and the value from the symbol table.

#### Implementation:
1) Simple expression that do not reference any variable are evaluated using means of python language and stored “.value” - attribute of a node. In case of strings they are just concatenated. In case of numbers everything is handled using python eval() function (saves from additional checks of operation symbol ). If value could’t be evaluated the node will store an “.error”-attribute and also “.lineno”.
2) The essential logic behind the implementation of the second level is explained in the beginning as a note. Compared to the simple expressions, nodes that are needed to be evaluated do not store error flags nor the line numbers due to complexity of implementation. All the values of variable saved within the symbol table in the following format: { “var_identifier” : value }

3) There are not much difference between implementing regular variables and tuples. The only difference is the content of lambda functions. Instead of normal arithmetic operations, the lambdas return python lists. Yes, tuple are implemented as lists in this interpreter, but the end user should not tell the difference. In case of “**” tuple, list is constructs using python list multiplications. In case of “..” - tuple, a list is constructed using generators.

4) The implementation of functions and the calls is slightly more complicated. The information from ASTNode of function definiton is moved to the symbol table and stored there as the dictionary. The function call are regular atoms that are always evaluable, have “params” and “args” -attributes. Args contain all the expression that can be either evaluable or to just have a value. Params contain parameters required for all the evaluable expression in args and a function identifier in addition. When the value of the function call – node is needed the following steps are done:
    1. Looking up the function information from the symbol table.
    2. Iterating through all the definitions/expression of the function.
    3. For those expression, lambdas of which require a value of function arguments, we first evaluate the expressions from the args of the function call (if needed) and save their values under corresponding keys in kwargs -dictionary. 
    4. All the expression evaluated using the passed dictionary and stored in the symbol table (under the scope of the function).
    5. The return_value – node of a function is evaluated and the value returned is saved to the function_call – node value.

6) Recursion is not implemented and it not clear, what was meant by proper local variables and parameters. Scoping was tested on the small examples with a global variable and the local function variable with the same name. The function return the variable. When there is a local variable its value is returned. When the local variable is removed, the value of the global variable is returned instead.


#### Features/Bugs:
Expression are evaluated starting from the end. For example an expression “7 – 2 + 3” will return “2”. (7 – 2 + 3 → 7 – 5 → 2). Curly braces should be used to force the desired execution order.
The return value of a function cannot be stored in a variable. Calls are supported from the program result value. Function that do not require evaluation might be stored. It was not tested.

#### Extra:
The language does not support the input of fractional and negative numbers. It is, however, possible to operate with them without a crash if an expression results in them.
