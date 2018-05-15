; ModuleID = 'samples/prog-b.bc'
source_filename = "samples/prog-b.bc"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@.str = private unnamed_addr constant [3 x i8] c"%d\00", align 1
@.str1 = private unnamed_addr constant [6 x i8] c"a > 0\00", align 1
@.str2 = private unnamed_addr constant [17 x i8] c"samples/prog-b.c\00", align 1
@__PRETTY_FUNCTION__.main = private unnamed_addr constant [11 x i8] c"int main()\00", align 1
@.str3 = private unnamed_addr constant [11 x i8] c"fact: %lu\0A\00", align 1

; Function Attrs: nounwind uwtable
define i64 @add(i32 %x, i32 %y) #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %r = alloca i64, align 8
  store i32 %x, i32* %1, align 4
  store i32 %y, i32* %2, align 4
  %3 = load i32, i32* %1, align 4
  %4 = load i32, i32* %2, align 4
  %5 = add nsw i32 %3, %4
  %6 = sext i32 %5 to i64
  store i64 %6, i64* %r, align 8
  %7 = load i64, i64* %r, align 8
  ret i64 %7
}

; Function Attrs: nounwind uwtable
define i32 @main() #0 {
  %1 = alloca i32, align 4
  %a = alloca i32, align 4
  %b = alloca i32, align 4
  %c = alloca i32, align 4
  store i32 0, i32* %1
  store i32 7, i32* %c, align 4
  br label %2

; <label>:2:                                      ; preds = %11, %0
  %3 = call i32 (i8*, ...) @__isoc99_scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i32 0, i32 0), i32* %a)
  %4 = icmp sgt i32 %3, 0
  br i1 %4, label %5, label %16

; <label>:5:                                      ; preds = %2
  %6 = load i32, i32* %a, align 4
  %7 = icmp sgt i32 %6, 0
  br i1 %7, label %8, label %9

; <label>:8:                                      ; preds = %5
  br label %11

; <label>:9:                                      ; preds = %5
  call void @__assert_fail(i8* getelementptr inbounds ([6 x i8], [6 x i8]* @.str1, i32 0, i32 0), i8* getelementptr inbounds ([17 x i8], [17 x i8]* @.str2, i32 0, i32 0), i32 15, i8* getelementptr inbounds ([11 x i8], [11 x i8]* @__PRETTY_FUNCTION__.main, i32 0, i32 0)) #3
  unreachable
                                                  ; No predecessors!
  br label %11

; <label>:11:                                     ; preds = %10, %8
  %12 = load i32, i32* %a, align 4
  %13 = load i32, i32* %c, align 4
  %14 = call i64 @add(i32 %12, i32 %13)
  %15 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([11 x i8], [11 x i8]* @.str3, i32 0, i32 0), i64 %14)
  br label %2

; <label>:16:                                     ; preds = %2
  ret i32 0
}

declare i32 @__isoc99_scanf(i8*, ...) #1

; Function Attrs: noreturn nounwind
declare void @__assert_fail(i8*, i8*, i32, i8*) #2

declare i32 @printf(i8*, ...) #1

attributes #0 = { nounwind uwtable "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { noreturn nounwind "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #3 = { noreturn nounwind }

!llvm.ident = !{!0}

!0 = !{!"Ubuntu clang version 3.6.2-3ubuntu2 (tags/RELEASE_362/final) (based on LLVM 3.6.2)"}
