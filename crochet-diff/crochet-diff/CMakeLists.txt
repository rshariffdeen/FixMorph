set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_library(crochetDiff
  lib/ASTDiff.cpp
  LINK_LIBS
  clangAST
  clangBasic 
  clangFrontend
  clangLex 
  clangRewrite 
  clangTooling
  clangToolingCore
  
  )


include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}
  include
  )


add_subdirectory(tool)

