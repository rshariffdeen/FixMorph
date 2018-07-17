set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_library(crochetPatch

  lib/ASTDiff.cpp
  lib/ASTPatch.cpp
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

