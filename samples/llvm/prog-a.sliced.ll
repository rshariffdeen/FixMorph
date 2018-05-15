; ModuleID = 'samples/prog-a.sliced'
source_filename = "samples/prog-a.bc"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@.str = private unnamed_addr constant [3 x i8] c"%d\00", align 1
@.str1 = private unnamed_addr constant [6 x i8] c"a > 0\00", align 1
@.str2 = private unnamed_addr constant [17 x i8] c"samples/prog-a.c\00", align 1
@__PRETTY_FUNCTION__.main = private unnamed_addr constant [11 x i8] c"int main()\00", align 1
@.str3 = private unnamed_addr constant [11 x i8] c"fact: %lu\0A\00", align 1

; Function Attrs: nounwind uwtable
define i32 @main() #0 {
  %a = alloca i32, align 4
  br label %1

; <label>:1:                                      ; preds = %4, %0
  %2 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i32 0, i32 0), i32* %a)
  %3 = icmp sgt i32 %2, 0
  br i1 %3, label %4, label %safe_return

; <label>:4:                                      ; preds = %1
  %5 = load i32, i32* %a, align 4
  %6 = icmp sgt i32 %5, 0
  br i1 %6, label %1, label %7

; <label>:7:                                      ; preds = %4
  call void @__assert_fail(i8* getelementptr inbounds ([6 x i8], [6 x i8]* @.str1, i32 0, i32 0), i8* getelementptr inbounds ([17 x i8], [17 x i8]* @.str2, i32 0, i32 0), i32 14, i8* getelementptr inbounds ([11 x i8], [11 x i8]* @__PRETTY_FUNCTION__.main, i32 0, i32 0)) #3
  unreachable

safe_return:                                      ; preds = %1
  ret i32 0
}

declare i32 @__isoc99_scanf(i8*, ...) #1

; Function Attrs: noreturn nounwind
declare void @__assert_fail(i8*, i8*, i32, i8*) #2

attributes #0 = { nounwind uwtable "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { noreturn nounwind "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #3 = { noreturn nounwind }

!llvm.ident = !{!0}

!0 = !{!"Ubuntu clang version 3.6.2-3ubuntu2 (tags/RELEASE_362/final) (based on LLVM 3.6.2)"}
