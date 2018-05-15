(define (fib n)
    (cond
      ((or (= n 0)  (= n 1)) n)
      (else
        (+ (fib (- n 1))
           (fib (- n 2))))))