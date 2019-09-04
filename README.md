# Crochet repair

The aim of this project is to find if...

### Prerequisites

Etherscan contract addresses
Use the 7428 samples from google docs excel: 
https://docs.google.com/spreadsheets/d/1OLrc1mwXTXOifgj072MzhQJ1qcLMB-R85HqCHlunJTY/edit#gid=1398248218 
Note that this sample size is fixed and no additional addresses will be added

A list of Github repos to be tested. 
This list is not fixed and additional repos might be added at a later time. 
In addition, an array of commit hashes must be made available for each repo used for reverting purposes

```Example```
Solidity contract ETH_VALUT from the following url:
https://etherscan.io/address/0xbaf51e761510c1a11bf48dd87c0307ac8a8c8a4f#code
This contract correspond to the etherscan address of 0xBaf51E761510C1a11Bf48dd87c0307aC8A8C8A4f

An example github repo is OpenZepplin, a library for secure smart contract development. The git address is:
https://github.com/OpenZeppelin/openzeppelin-solidity.git

After downloading the git, we can view the commit history through the command:
git log
And list its commit hashes through:
git log --pretty=format:%H
```

## Getting Started

Etherscan contract addresses 
We can create a dictionary of the 7428 contract addresses with their content hashe. The content will be the corresponding function with no spaces in between. 
Using the fact that the word 'contract' is a keyword indicating the start of a contract source code, we will denote the de-spaced codes between any 2 of these keywords( or 'contract' with any other keywords ) as the contract source code of the leading contract to be hashed. 

Any Github repos to be tested (And their commits)
Assumption made: Only files ending with extension .sol is to be tested upon. These files normally resides in the folder 'contracts'
Before any preprocessing is to be made, the files should be cleaned from unnecessary content for faster access. We can isolate these unnecessary content through the use of keywords such as 'pragma', 'import' or the comment indicating words '/*'. The final document to be tested should contain the keyword 'contract' only

## Program to be used

Python3 is suffice for this operation.

## Proposed method:
With two dictionaries: one of Etherscan addresses and the other of repos and their constituting contracts (de-spaced and hashed ), we can lookup if there are identical contracts between the Etherscan addresses and the repos(and the commits as well). The end result should be an array of length 7428 for each repo indicating if the contract is present in the contract.

To increase efficiency, we can arrange the commits in the order of decreasing number of contracts present. In this way, should one of the commit indicate the presence of a contract from the Etherscan addresses dictionary, there is no need to look further into the other commits


## Versioning

## Authors

* **Lin Xu** - *Initial work* - 

## License


## Acknowledgments

