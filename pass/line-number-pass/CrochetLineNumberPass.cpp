#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/IR/DebugInfoMetadata.h"
using namespace llvm;

namespace {

  class CrochetFunction {
      int first, last;
  public:

      void setValues(int x, int y){
          first = x;
          last = y;
      }

      int getFirst(){
          return first;
      }

      int getLast(){
          return last;
      }


  };

  struct CrochetLineNumberPass : public FunctionPass {
    static char ID;
      CrochetLineNumberPass() : FunctionPass(ID) {}
      std::map<std::string, CrochetFunction> functionRange;
    virtual bool runOnFunction(Function &F) {
        errs() << "In a function called " << F.getName() << "!\n";
        bool firstInstruction = true;
        unsigned firstLineNumber = 0;
        unsigned lastLineNumber = 0;


        for (auto &B : F) {
            for (auto &I : B) {
                if (firstInstruction){
                    if (DILocation *Loc = I.getDebugLoc()) { // Here I is an LLVM instruction
                        firstInstruction = false;
                        firstLineNumber = Loc->getLine();
                    }
                }

                if (isa<ReturnInst>(I)){
                    if (DILocation *Loc = I.getDebugLoc()) { // Here I is an LLVM instruction
                        lastLineNumber = Loc->getLine();
                    }
                }

            }
        }

        CrochetFunction functionInfo;
        functionInfo.setValues(firstLineNumber,lastLineNumber);
        functionRange[F.getName()] = functionInfo ;

      return false;
    }
  };
}

char CrochetLineNumberPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerCrochetLineNumberPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new CrochetLineNumberPass());
}
static RegisterStandardPasses
  RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                 registerCrochetLineNumberPass);
