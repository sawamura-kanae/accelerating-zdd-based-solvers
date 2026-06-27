#lang racket

(provide (all-defined-out))

(require (for-syntax syntax/parse))

;; Clojure thread macros

(define-syntax -->
  (syntax-rules ()
    [(_ init) init]
    [(_ acc (f args ...) rst ...) (--> (f acc args ...) rst ...)]
    [(_ acc f rst ...) (--> (f acc) rst ...)]))

(define-syntax ->>
  (syntax-rules ()
    [(_ init) init]
    [(_ acc (f args ...) rst ...) (->> (f args ... acc) rst ...)]
    [(_ acc f rst ...) (->> (f acc) rst ...)]))

(define-syntax (as-> stx)
  (syntax-parse stx
    [(_ init:expr bind:id) #'init]
    [(_ acc:expr bind:id arg:expr args:expr ...)
     #'(let ([bind acc]) (as-> arg bind args ...))]))
