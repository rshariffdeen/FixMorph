// Copyright (C) 2012 Eric Schulte                         -*- C++ -*-
#ifndef DRIVER_ASTMUTATORS_H
#define DRIVER_ASTMUTATORS_H

#include "clang/Basic/LLVM.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/ASTContext.h"

namespace clang {  

enum ACTION { NUMBER, IDS, ANNOTATOR, LISTER, CUT, DELETE, INSERT, SWAP, GET, SET, VALUEINSERT, UPDATE, MOVE };



ASTConsumer *CreateASTSwapper(unsigned int Stmt1, unsigned int Stmt2);

ASTConsumer *CreateASTInserter(unsigned int Line, unsigned int Column, StringRef SearchQuery, StringRef InsertQuery, unsigned int Offset);
ASTConsumer *CreateASTUpdater(unsigned int Line, unsigned int Column, StringRef SearchQuery, StringRef ReplaceQuery);
ASTConsumer *CreateASTRemover(unsigned int Line, unsigned int Column, StringRef Query);
ASTConsumer *CreateASTMover(unsigned int Line, unsigned int Column, StringRef Query, StringRef MoveQuery);

}

#endif
