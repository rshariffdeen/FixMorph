# Example Usage
In this document we provide examples of how to use FixMorph with prepared 
test cases to elaborate the capabilities of FixMorph. Following details explain
the test-cases we provide in our repository. Please take a look at the
page Getting Started to understand how to use FixMorph. 


### Example of line number difference
    python3.7 FixMorph.py --conf=tests/insert/different-line/repair.conf

### Example of contextual-difference
    python3.7 FixMorph.py --conf=tests/insert/different-context/repair.conf

### Example of adapting membership expressions
    python3.7 FixMorph.py --conf=tests/insert/member-expr/repair.conf

### Example of updating an argument to an API call
    python3.7 FixMorph.py --conf=tests/update/method-arg/repair.conf

### Example of updating an API call
    python3.7 FixMorph.py --conf=tests/update/method-call/repair.conf

### Example of importing/transplanting missing dependency
    python3.7 FixMorph.py --conf=tests/insert/missing-dependency/repair.conf

### Example of using global context for API mapping
    python3.7 FixMorph.py --conf=tests/insert/method-call/repair.conf

