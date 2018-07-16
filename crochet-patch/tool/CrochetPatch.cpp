//===--------------- clang-mutate.cpp - Clang mutation tool ---------------===//
//
// Copyright (C) 2012 Eric Schulte
//
//===----------------------------------------------------------------------===//
//
//  This file implements a mutation tool that runs a number of
//  mutation actions defined in ASTMutate.cpp over C language source
//  code files.
//
//  This tool uses the Clang Tooling infrastructure, see
//  http://clang.llvm.org/docs/LibTooling.html for details.
//
//===----------------------------------------------------------------------===//
#include "crochet-patch/Tooling/ASTMutate.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/Driver/Options.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/CommandLine.h"

using namespace clang::driver;
using namespace clang::tooling;
using namespace llvm;


// Apply a custom category to all command-line options so that they are the
// only ones displayed.
static llvm::cl::OptionCategory MutateToolCategory("mutate-tool options");

static cl::extrahelp CommonHelp(CommonOptionsParser::HelpMessage);
static cl::extrahelp MoreHelp(
    "Example Usage:\n"
    "\n"
    "\tto delete node in line:\n"
    "\n"
    "\t  ./crochet-patch -delete -line=123 -query='VarDecl: int i=0' source_file.c\n"
    "\n"
    "\tto update node in line:\n"
    "\n"
    "\t  ./crochet-patch -update -line=123 -query='VarDecl: int i=0' -value='int j=1' source_file.c\n"
    "\n"
    "\tto insert node in line:\n"
    "\n"
    "\t  ./crochet-patch -insert -line=123 -query='CompoundStm' -offset=5 -value='int j=1' source_file.c\n"
    "\n"
);


static cl::opt<bool>             Delete ("delete",       cl::desc("delete node in line"));
static cl::opt<bool>             Update ("update",       cl::desc("update node in line"));
static cl::opt<bool>             Insert ("insert",       cl::desc("insert node in line"));
static cl::opt<bool>               Move ("move",         cl::desc("move node position"));
static cl::opt<unsigned int>       Line ("line",         cl::desc("line number to identify search node"));
static cl::opt<unsigned int>     Column ("column",       cl::desc("column number to identify search node"));
static cl::opt<unsigned int>     Offset ("offset",       cl::desc("offset for update/insert operation"));
static cl::opt<std::string>    NewValue ("value",        cl::desc("string value for update/insert operations"), cl::init(""));
static cl::opt<std::string>       Query ("query",        cl::desc("query for operation"), cl::init(""));
static cl::opt<std::string>  ScriptPath ("script-path",  cl::desc("path for the ast edit script"), cl::init(""));



class MutationConsumer : public clang::ASTConsumer {
public: 
       
      clang::ASTConsumer *newASTConsumer() {
        if (Delete){          
          return clang::CreateASTRemover(Line, Column, Query);
        }

        if (Update){
          return clang::CreateASTUpdater(Line, Column, Query, NewValue);
        }

        if (Insert){     
          return clang::CreateASTInserter(Line, Column, Query, NewValue, Offset);
        }
        if (Move){
          return clang::CreateASTMover(Line, Column, Query, NewValue);
        }

        
        errs() << "Must supply one of following operations;";     
        errs() << "\tinsert\n";
        errs() << "\tupdate\n";
        errs() << "\tdelete\n";
        errs() << "\tmove\n";
        errs() << "\tinsert-value\n";
        exit(EXIT_FAILURE);
    }
  
};

class MutationAction : public clang::ASTFrontendAction {
public:

    MutationAction() {}       
    std::unique_ptr<clang::ASTConsumer> CreateASTConsumer(
    clang::CompilerInstance &Compiler, llvm::StringRef InFile) override {    
    MutationConsumer *consumer = new MutationConsumer();  
    return std::unique_ptr<clang::ASTConsumer>(consumer->newASTConsumer());

  }
};



int main(int argc, const char **argv) {  
  CommonOptionsParser OptionsParser(argc, argv, MutateToolCategory);
  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());
  
  Tool.run(newFrontendActionFactory<MutationAction>().get());
  return 0;
  
}
