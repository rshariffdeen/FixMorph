set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_executable(crochet-diff
  CrochetDiff.cpp
  )

target_link_libraries(crochet-diff
  PRIVATE
  crochetDiff
  clangBasic
  clangFrontend
  clangRewrite
  clangTooling 
  clangToolingCore
  )

install(TARGETS crochet-diff
  RUNTIME DESTINATION bin)
