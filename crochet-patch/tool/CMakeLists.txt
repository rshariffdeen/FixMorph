set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_executable(crochet-patch
  CrochetPatch.cpp
  )

target_link_libraries(crochet-patch
  PRIVATE
  crochetPatch
  clangBasic
  clangFrontend
  clangRewrite
  clangTooling 
  clangToolingCore
  )

install(TARGETS crochet-patch
  RUNTIME DESTINATION bin)
